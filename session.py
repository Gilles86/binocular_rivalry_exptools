from exptools.core import Session, MRISession
from exptools import config
from trial import CalibrateTrial, WaitTrial, RDMTrial, FlickerTrial, RDMCalibrateTrial, MRITriggerWaitTrial, FixationTrial
from psychopy import clock, visual
import os
import exptools
import json

from psychopy import logging
from psychopy.data import QuestHandler, MultiStairHandler
import numpy as np
logging.console.setLevel(logging.CRITICAL)

class CalibrateSession(MRISession):


    def __init__(self, *args, **kwargs):

        super(CalibrateSession, self).__init__(*args, **kwargs)

        self.create_screen(full_screen=False, engine='psychopy')

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

        self.no_response_stimulus = visual.TextStim(self.screen, "No Response!", color='white', height=70)
        self.correct_stimulus = visual.TextStim(self.screen, "Correct!", color='green', height=70)
        self.error_stimulus = visual.TextStim(self.screen, "Error!", color='red', height=70)


    def run(self):
        """docstring for fname"""
        # cycle through trialsgamma


        print self.screen.gamma

        self.parameters['coherence'] = .5

        blue_intensity_fn = 'data/blue_intensity_%s.txt' % self.subject_initials
        red_intensity_fn = 'data/red_intensity_%s.txt' % self.subject_initials


        # BLUE INTENSITY CALIBRATION
        if not os.path.exists(blue_intensity_fn):
            text = "Please close your left eye and indicate whether you see the\ncloud of dots _clearly_."
            trial = WaitTrial(text, session=self, screen=self.screen)
            trial.run()
            conditions=[
                {'label':'low', 'startVal': .1, 'minVal':0, 'maxVal':1.},
                {'label':'high','startVal': .9, 'minVal':0, 'maxVal':1.}]

            q = MultiStairHandler('simple', conditions=conditions, nTrials=35)
            for i, (blue_intensity, condition) in enumerate(q):
                blue_intensity = blue_intensity * 2 - 1
                print blue_intensity
                if not self.stopped:
                    self.parameters['blue_intensity'] = blue_intensity
                    self.parameters['direction'] = np.random.rand() * 360

                    trial = RDMCalibrateTrial(i+1, self.parameters, screen=self.screen, session=self)
                    trial.run()
                    print trial.parameters['seen']
                    if not self.stopped and 'seen' in trial.parameters:
                        q.addResponse(int(trial.parameters['seen']))

                else:
                    break   

            
            if not os.path.exists('data'):
                os.makedirs('data')

            np.savetxt(blue_intensity_fn, [self.parameters['blue_intensity'] / 2 + .5])
        
        self.parameters['blue_intensity'] = np.loadtxt(blue_intensity_fn)

        text = "Blue intensity set at %.2f\nPress any key to continue" % self.parameters['blue_intensity']
        trial = WaitTrial(text, session=self, screen=self.screen)
        trial.run()


        # RED INTENSITY CALIBRATION
        if not os.path.exists(red_intensity_fn):
            text = "Press left if the stimulus moves counterclockwise, right if it moves clockwise."
            trial = WaitTrial(text, session=self, screen=self.screen)
            trial.run()
            self.frame_rate = 60
            self.parameters['frequency'] = 6
            self.parameters['duration'] = 1000
            self.parameters['color2'] = np.array((self.parameters['blue_intensity'], 0, 0))
            self.parameters['color1'] = np.array((0, 0, self.parameters['blue_intensity']))

            self.parameters['light_gray'] = [self.parameters['blue_intensity'] * .7, 0, self.parameters['blue_intensity'] * .8]
            self.parameters['dark_gray'] = [self.parameters['blue_intensity'] * .3, 0, self.parameters['blue_intensity'] * .3]

            conditions=[
                {'label':'low', 'startVal': 0.0, 'minVal':0., 'maxVal':self.parameters['blue_intensity'], 'startValSd':0.025, 'gamma':0.01, 'pThreshold':0.63},
                {'label':'low', 'startVal': 0.0, 'minVal':0., 'maxVal':self.parameters['blue_intensity'], 'startValSd':0.025, 'gamma':0.01, 'pThreshold':0.63}]

            q = MultiStairHandler('quest', conditions=conditions, nTrials=35)

            for i, (red_intensity, condition) in enumerate(q):
                if not self.stopped:
                    print red_intensity, self.parameters['blue_intensity']
                    self.parameters['color1'] = (0, 0, self.parameters['blue_intensity'])#/2 - 1)
                    self.parameters['color2'] = (red_intensity, 0, 0)
                    self.parameters['fixation_duration'] = np.random.exponential(1., 1)

                    trial = CalibrateTrial(1, self.parameters, session=self, screen=self.screen)
                    trial.run()


                    if not self.stopped and 'brightest_color' in trial.parameters:
                        q.addResponse(int(trial.parameters['brightest_color'] == 'color_1'))
                else:
                    break

                self.parameters['red_intensity'] = (q.staircases[0].mode() + q.staircases[1].mode()) / 2
                np.savetxt(red_intensity_fn, [self.parameters['red_intensity']])

        self.parameters['red_intensity'] = np.loadtxt(red_intensity_fn)
        text = "Red intensity set at %.2f\nPress any key to continue" % self.parameters['red_intensity']
        trial = WaitTrial(text, session=self, screen=self.screen)
        trial.run()

        # Actual experiment
        while not self.stopped:
            self.current_tr = 0
            text = 'Waiting for trigger'
            trial = MRITriggerWaitTrial(text, session=self, screen=self.screen)
            trial.run()

            self.current_tr = 0
            self.scanning = True
            
            self.parameters['block'] = 0
            while self.scanning and (not self.stopped):

                trial_idx = 1
                self.parameters['trial_type'] = np.random.choice(['red', 'blue', 'both'])
                print 'RANDOM CHOICE'

                self.parameters['block'] += 1

                if self.parameters['trial_type'] == 'red':
                    self.parameters['color'] = (self.parameters['red_intensity'] * 2 - 1, -1, -1)
                elif self.parameters['trial_type'] == 'blue':
                    self.parameters['color'] = (-1, -1, self.parameters['blue_intensity'] * 2 - 1)
                elif self.parameters['trial_type'] == 'both':
                    self.parameters['color'] = ((self.parameters['red_intensity'] - 1), -1, (self.parameters['blue_intensity'] - 1))

                while (self.current_tr % 6 < 4) and self.scanning:

                    self.parameters['direction'] = np.random.choice([180, 0])
                    self.parameters['coherence'] = np.random.choice([0, 0.06, 0.12, 0.24, 0.48])

                    trial = RDMTrial(trial_idx, self.parameters, screen=self.screen, session=self)
                    trial.run()
                    trial_idx += 1

                    if (self.clock.getTime() - self.time_of_last_tr) > 10:
                        self.scanning = False

                while (self.current_tr % 6 > 3) and self.scanning:
                    self.parameters['trial_type'] = 'fixation'
                    self.parameters['coherence'] = None
                    self.parameters['direction'] = None

                    trial = FixationTrial(trial_idx, self.parameters, screen=self.screen, session=self)
                    trial.run()

                    if (self.clock.getTime() - self.time_of_last_tr) > 10:
                        self.scanning = False


        self.close()


    def mri_trigger(self):
        print self.current_tr

        super(CalibrateSession, self).mri_trigger()
