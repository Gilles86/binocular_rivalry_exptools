from exptools.core import Session
from exptools import config
from trial import CalibrateTrial, WaitTrial, RDMTrial, FlickerTrial
from psychopy import clock, visual
import os
import exptools
import json

from psychopy import logging
from psychopy.data import QuestHandler, MultiStairHandler
import numpy as np
logging.console.setLevel(logging.CRITICAL)

class CalibrateSession(Session):


    def __init__(self, *args, **kwargs):

        super(CalibrateSession, self).__init__(*args, **kwargs)

        self.create_screen(full_screen=True, engine='psychopy')

        # Set up parameters
        config_file = os.path.join(os.path.abspath(os.getcwd()), 'default_settings.json')

        with open(config_file) as config_file:
            config = json.load(config_file)
        
        self.parameters = config
        self.refresh_rate = self.screen.getActualFrameRate()

        if self.parameters['n_trials'] % 2 != 0:
            raise Exception('Please, even number of trials per block')

        self.stopped = False
        self.pausing = False

        self.n_trials = self.parameters['n_trials']



    def run(self):
        """docstring for fname"""
        # cycle through trialsgamma


        print self.screen.gamma

        self.parameters['coherence'] = .5

        blue_intensity_fn = 'data/blue_intensity_%s.txt' % self.subject_initials

        if not os.path.exists(blue_intensity_fn):
            conditions=[
                {'label':'low', 'startVal': 0.3, 'minVal':0., 'maxVal':1., 'stepSizes':0.05, 'stepType':'lin'},
                {'label':'high','startVal': 0.7, 'minVal':0., 'maxVal':1., 'stepSizes':0.05, 'stepType':'lin'}]

            q = MultiStairHandler('simple', conditions=conditions, nTrials=5)
            for i, (blue_intensity, condition) in enumerate(q):
                print blue_intensity
                if not self.stopped:
                    self.parameters['blue_intensity'] = blue_intensity
                    self.parameters['direction'] = np.random.rand() * 360

                    trial = RDMTrial(i+1, self.parameters, screen=self.screen, session=self)
                    trial.run()
                    if not self.stopped and 'seen' in trial.parameters:
                        q.addResponse(int(trial.parameters['seen']))

                else:
                    break   

            
            if not os.path.exists('data'):
                os.makedirs('data')

            np.savetxt(blue_intensity_fn, [self.parameters['blue_intensity']])
        
        self.parameters['blue_intensity'] = np.loadtxt(blue_intensity_fn)
        text = "Blue intensity set at %.2f\nPress any key to continue" % self.parameters['blue_intensity']
        trial = WaitTrial(text, session=self, screen=self.screen)
        trial.run()

        self.frame_rate = 60
        self.parameters['frequency'] = 6
        self.parameters['duration'] = 1000
        self.parameters['color2'] = np.array((self.parameters['blue_intensity'], 0, 0))
        self.parameters['color1'] = np.array((0, 0, self.parameters['blue_intensity']))

        self.parameters['light_gray'] = [self.parameters['blue_intensity'] * .7, 0, self.parameters['blue_intensity'] * .8]
        self.parameters['dark_gray'] = [self.parameters['blue_intensity'] * .3, 0, self.parameters['blue_intensity'] * .3]

        trial = CalibrateTrial(1, self.parameters, session=self, screen=self.screen)
        trial.run()

        self.parameters['color1'] = (-1.0, -1.0, self.parameters['blue_intensity'])#/2 - 1)
        self.parameters['color2'] = (self.parameters['blue_intensity'], -1.0, -1.0)

        trial = FlickerTrial(1, self.parameters, session=self, screen=self.screen)
        trial.run()

        self.close()
