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


# IntensityThresholdSession
# EquiluminanceCalibrateSession
# RDMSession
# WaitSession

class MySession(Session):

    def __init__(self, *args, **kwargs):
            
        config_file = os.path.join(os.path.abspath(os.getcwd()), 'default_settings.json')

        with open(config_file) as config_file:
            config = json.load(config_file)
        self.parameters = config

        self.create_screen(full_screen=False, engine='psychopy')
        self.frame_rate = self.screen.getActualFrameRate()

        super(MySession, self).__init__(*args, **kwargs)

class IntensityThresholdSession(MySession):

    def __init__(self, subj_idx, trial_idx, color, *args, **kwargs):
        super(IntensityThresholdSession, self).__init__(subj_idx, trial_idx, *args, **kwargs)
        self.parameters['coherence'] = self.parameters['calibrate_coherence']

    def run(self):
        text = "Please close your left eye and indicate whether you see the\ncloud of dots _clearly_."
        trial = WaitTrial(text, session=self, screen=self.screen)
        trial.run()
        conditions=[
            {'label':'low', 'startVal': .1, 'minVal':0, 'maxVal':1.},
            {'label':'high','startVal': .9, 'minVal':0, 'maxVal':1.}]

        q = MultiStairHandler('simple', conditions=conditions, nTrials=2)
        for i, (blue_intensity, condition) in enumerate(q):
            blue_intensity = blue_intensity * 2 - 1
            print blue_intensity
            if not self.stopped:
                self.parameters['blue_intensity'] = blue_intensity
                self.parameters['direction'] = np.random.rand() * 360

                trial = RDMCalibrateTrial(i+1, self.parameters, screen=self.screen, session=self)
                trial.run()

                if not self.stopped and 'seen' in trial.parameters:
                    print trial.parameters['seen']
                    q.addResponse(int(trial.parameters['seen']))

            else:
                break   

        return self.parameters['blue_intensity'] / 2 + .5
        
class EquiluminanceCalibrateSession(MySession):

    def __init__(self, subj_idx, trial_idx, color1, color2,  *args, **kwargs):
        super(EquiluminanceCalibrateSession, self).__init__(subj_idx, trial_idx, *args, **kwargs)
        self.parameters['color1'] = np.array(color1)
        self.parameters['start_color2'] = np.array(color2)

        self.parameters['light_gray'] = .5 * (self.parameters['color1'] + self.parameters['start_color2'])
        self.parameters['dark_gray'] = .25 * (self.parameters['color1'] + self.parameters['start_color2'])

        self.parameters['frequency'] = 6
        self.parameters['duration'] = 1000


    def run(self):

        text = "Press left if the stimulus moves counterclockwise, right if it moves clockwise."
        trial = WaitTrial(text, session=self, screen=self.screen)
        trial.run()


        conditions=[
            {'label':'low', 'startVal': 0.73, 'minVal':0.0, 'stepType':'db', 'stepSizes':[4, 3, 2, 1], 'nUp':1, 'nDown':1},
            {'label':'high', 'startVal': .73, 'minVal':0.0, 'stepType':'db', 'stepSizes':[4,3,2,1],'nUp':1, 'nDown':1},
        ]

        q = MultiStairHandler('simple', conditions=conditions, nTrials=20)
        #q = StairHandler(0.5, 2, nUp=1, nDown=1, stepType='lin', stepSize=0.02, nTrials=35)

        for i, (intensity, condition) in enumerate(q):
            print intensity
            if not self.stopped:
                self.parameters['color2'] = intensity * self.parameters['start_color2']
                self.parameters['fixation_duration'] = np.random.exponential(1., 1)

                trial = CalibrateTrial('calibrate_%s' % i, self.parameters, session=self, screen=self.screen)
                trial.run()


                if not self.stopped and 'brightest_color' in trial.parameters:
                    q.addResponse(int(trial.parameters['brightest_color'] == 'color_1'))
            else:
                break

        self.parameters['threshold_intensity'] = (np.mean(q.staircases[0].intensities) + np.mean(q.staircases[1].intensities)) / 2
        return self.parameters['threshold_intensity']

class MRIWaitSession(MySession, MRISession):

    def __init__(self, subj_idx, run_idx, text, *args, **kwargs):
        super(MRIWaitSession, self).__init__(subj_idx, run_idx, *args, **kwargs)
        self.trial = MRITriggerWaitTrial(text='Waiting for MRI trigger', screen=self.screen, session=self)


    def run(self):
        self.trial.run()

class RDMSession(MySession, MRISession):

    def __init__(self, subj_idx, run_idx, color1, color2, sum_intensity, *args, **kwargs):

        self.color1 = np.array(color1) * 2 - 1
        self.color2 = np.array(color2) * 2 - 1
        self.color12 = (sum_intensity * (np.array(color1) + np.array(color2))) * 2 - 1

        super(RDMSession, self).__init__(subj_idx, run_idx, *args, **kwargs)


    def run(self):
        while not self.stopped:
            self.current_tr = 0
            text = 'Starting...'
            trial = MRITriggerWaitTrial(text, session=self, screen=self.screen)
            trial.run()

            self.scanning = True
            
            self.parameters['block'] = 0
            self.parameters['run'] = self.index_number

            while self.scanning and (not self.stopped):

                trial_idx = 1
                self.parameters['trial_type'] = np.random.choice(['color1', 'color2', 'color12'])
                self.parameters['block'] += 1
                print self.parameters, self.color12

                if self.parameters['trial_type'] == 'color1':
                    self.parameters['color'] = self.color1
                elif self.parameters['trial_type'] == 'color2':
                    self.parameters['color'] = self.color2
                elif self.parameters['trial_type'] == 'color12':
                    self.parameters['color'] = self.color12

                while (self.current_tr % 6 < 4) and self.scanning and not self.stopped:

                    self.parameters['direction'] = np.random.choice([180, 0])
                    self.parameters['coherence'] = np.random.choice([0, 0.06, 0.12, 0.24, 0.48])
                    self.parameters['fixation_color'] = self.color12

                    trial = RDMTrial(trial_idx, self.parameters, screen=self.screen, session=self)
                    trial.run()
                    trial_idx += 1

                    if (self.clock.getTime() - self.time_of_last_tr) > 10:
                        self.scanning = False

                while (self.current_tr % 6 > 3) and self.scanning and not self.stopped:
                    self.parameters['trial_type'] = 'fixation'
                    self.parameters['coherence'] = None
                    self.parameters['direction'] = None

                    self.parameters['color'] = self.color12

                    trial = FixationTrial(trial_idx, self.parameters, screen=self.screen, session=self)
                    trial.run()

                    if (self.clock.getTime() - self.time_of_last_tr) > 10:
                        self.scanning = False


        self.close()

class CalibrateSession(MRISession):


    def __init__(self, *args, **kwargs):

        super(CalibrateSession, self).__init__(*args, **kwargs)

        self.create_screen(full_screen=False, engine='psychopy')

        # Set up parameters
        config_file = os.path.join(os.path.abspath(os.getcwd()), 'default_settings.json')

        with open(config_file) as config_file:
            config = json.load(config_file)
        
        self.parameters = config
        self.frame_rate = self.screen.getActualFrameRate()

        if self.parameters['n_trials'] % 2 != 0:
            raise Exception('Please, even number of trials per block')

        self.stopped = False
        self.pausing = False

        self.n_trials = self.parameters['n_trials']

    def run(self):
        """docstring for fname"""
        # cycle through trialsgamma


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
                {'label':'low', 'startVal': 0.4, 'minVal':self.parameters['blue_intensity'] * .9, 'maxVal':self.parameters['blue_intensity'], 'startValSd':0.1, 'gamma':0.01, 'pThreshold':0.63, 'stepType':'lin', 'stepSize':0.025},
                {'label':'low', 'startVal': 0.8, 'minVal':0., 'maxVal':self.parameters['blue_intensity'], 'startValSd':0.025, 'gamma':0.01, 'pThreshold':0.63, 'stepType':'lin', 'stepSize':0.025}]

            q = MultiStairHandler('simple', conditions=conditions, nTrials=35)
            q = StairHandler(0.5, 2, nUp=1, nDown=1, stepType='lin', stepSize=0.02, nTrials=35)

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

            self.parameters['red_intensity'] = (np.mean(q.staircases[0].intensities) + np.mean(q.staircases[1].intensities)) / 2
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
