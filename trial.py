from exptools.core.trial import Trial
import os
import exptools
import json
from psychopy import logging, visual, event
import numpy as np
from stimulus import create_stimulus, RDMStimulus

class WaitTrial(Trial):

    def __init__(self, text=None, *args, **kwargs):
        super(WaitTrial, self).__init__(phase_durations=[10000], *args, **kwargs)
        self.ID = 'instruction'
        self.text = visual.TextStim(self.screen, text=text, color='white', height=50, wrapWidth=500)

    def draw(self):
        self.text.draw()
        super(WaitTrial, self).draw()

    def key_event(self, key):
        super(WaitTrial, self).key_event(key)

        self.stop()

        if key == 'q':
            self.session.stop()



class CalibrateTrial(Trial):

    def __init__(self, trial_idx, parameters, blocksize=360, *args, **kwargs):

        phase_durations = [parameters['duration']]

        super(CalibrateTrial, self).__init__(parameters=parameters,
                                             phase_durations=phase_durations,
                                             *args, 
                                             **kwargs)
        self.n_frames_per_stimulus =  self.session.frame_rate / self.parameters['frequency']

        self.make_stimuli()
        size_fixation_pix = self.session.deg2pix(self.parameters['size_fixation_deg'])

        self.fixation = visual.GratingStim(self.screen, 
                                           tex='cross', 
                                           mask='circle', 
                                           size=size_fixation_pix, 
                                           texRes=512, 
                                           color='white', 
                                           sf=0)


        self.ID = trial_idx
        self.t = 0


    def make_stimuli(self):
        self.stimulus1 = create_stimulus(self.screen, 
                                         self.parameters['color1'],
                                         self.parameters['color2'])

        self.stimulus2 = create_stimulus(self.screen, 
                                         self.parameters['dark_gray'],
                                         self.parameters['light_gray'],
                                         phase=90)

        self.stimulus3 = create_stimulus(self.screen, 
                                         self.parameters['color1'],
                                         self.parameters['color2'],
                                         phase=180)

        self.stimulus4 = create_stimulus(self.screen, 
                                         self.parameters['dark_gray'],
                                         self.parameters['light_gray'],
                                         phase=270)
        self.stimuli = [self.stimulus1,
                        self.stimulus2,
                        self.stimulus3,
                        self.stimulus4]

    def draw(self, *args, **kwargs):
        self.stimuli[self.t / self.n_frames_per_stimulus % (len(self.stimuli))].draw()
        self.t += 1
        self.fixation.draw()
        super(CalibrateTrial, self).draw()


    def run(self):
        super(CalibrateTrial, self).run()

    def stop(self):
        self.stopped = True
        super(CalibrateTrial, self).stop()

    def key_event(self, key):

        if key in ['esc', 'escape', 'q']:
            self.events.append([-99,self.session.clock.getTime()-self.start_time])

            self.session.logging.info('run canceled by user')
            self.session.stop()
            self.stop()

        if key in ['esc', 'escape', 'q']:
            self.events.append([-99,self.session.clock.getTime()-self.start_time])
            self.session.logging.info('run canceled by user')
            self.session.stop()
            self.stop()
        if key == 'z':
            #self.parameters['color2'] *= 1./0.95
            self.parameters['color2'][0] += 0.05
            self.parameters['light_gray'] = (self.parameters['color1'] + self.parameters['color2']) * .5
            self.parameters['dark_gray'] = (self.parameters['color1'] + self.parameters['color2']) * 0.1
            self.make_stimuli()
            print self.stimuli[1].image.mean(0).mean(0)

        if key == 'm':
            #self.parameters['color2'] *= 0.95/1.
            self.parameters['color2'][0] -= 0.05
            self.parameters['light_gray'] = (self.parameters['color1'] + self.parameters['color2']) * 0.5
            self.parameters['dark_gray'] = (self.parameters['color1'] + self.parameters['color2']) * 0.1
            self.make_stimuli()

        super(CalibrateTrial, self).key_event(key)


class RDMTrial(Trial):

    def __init__(self, trial_idx, parameters, *args, **kwargs):

        fixation_time = np.random.exponential(parameters['fixation_time'])
            
        phase_durations = [fixation_time, parameters['stimulus_time'], 10000]

        super(RDMTrial, self).__init__(parameters=parameters,
                                         phase_durations=phase_durations,
                                         *args, 
                                         **kwargs)

        self.ID = trial_idx

        fieldSize = self.session.deg2pix(self.parameters['fieldsize_deg'])
        dotDensity = self.parameters['dot_density'] / self.session.pixels_per_degree**2

        fieldArea = (fieldSize/2)**2 * np.pi
        nDots = int(fieldArea * dotDensity)

        speed = self.session.deg2pix(self.parameters['speed']) / self.session.refresh_rate

        dotSize = np.max([int(self.session.deg2pix(self.parameters['dot_size'])), 1])

        self.stimuli = visual.ElementArrayStim(self.screen,
                                          nElements=nDots,
                                          sizes=dotSize, 
                                          units='pix',
                                          elementTex=None,
                                          elementMask="circle",
                                          fieldShape='circle',
                                          colors=(-1.0, -1.0, self.parameters['blue_intensity']),     
                                          colorSpace='rgb',
                                          fieldSize=(fieldSize, fieldSize),)

        self.dot_stimulus = RDMStimulus(self.screen,
                                        self.stimuli,
                                        direction=self.parameters['direction'],
                                        coherence=self.parameters['coherence'],
                                        speed=speed)


        size_fixation_pix = self.session.deg2pix(self.parameters['size_fixation_deg'])

        self.fixation = visual.GratingStim(self.screen, 
                                               tex='sin', 
                                               mask='circle', 
                                               size=size_fixation_pix, 
                                               texRes=512, 
                                               color='white', 
                                               sf=0)

        self.text = visual.TextStim(self.screen, 'Did you see the stimulus? (left = no, right = yes)')


    def draw(self, *args, **kwargs):

        if self.phase == 0:
            self.fixation.draw()
        elif self.phase == 1:    
            self.dot_stimulus.draw()
            #self.stimuli.draw()
            self.fixation.draw()

        elif self.phase == 2:
            self.text.draw()

        super(RDMTrial, self).draw()


    def run(self):

        self.start_time = self.session.clock.getTime()
        self.parameters['start_time'] = self.start_time

        while not self.stopped:
            
            # events and draw
            self.event()
            self.draw()

            if self.phase == 0:
                if self.session.clock.getTime() - self.start_time > self.phase_times[0]:
                    self.phase_forward()

            if self.phase == 1:
                if self.session.clock.getTime() - self.start_time > self.phase_times[1]:
                    self.phase_forward()
            
    
        self.stop()

    def stop(self):
        super(RDMTrial, self).stop()

    def key_event(self, key):

        if key in ['esc', 'escape', 'q']:
            self.events.append([-99,self.session.clock.getTime()-self.start_time])
            self.session.logging.info('run canceled by user')
            self.session.stop()
            self.stop()

        if key == 'p':
            self.session.pausing = True

        if self.phase == 2:
            if key == 'z':
                self.parameters['seen'] = False
            elif key == 'm':
                self.parameters['seen'] = True

            self.stop()

        super(RDMTrial, self).key_event(key)


class FlickerTrial(Trial):


    def __init__(self, text=None, *args, **kwargs):
        super(FlickerTrial, self).__init__(phase_durations=[10000], *args, **kwargs)
        self.ID = 'instruction'
        self.text = visual.TextStim(self.screen, text=text, color='white', height=50, wrapWidth=500)
        self.stimulus1 = visual.Rect(self.screen, self.screen.size[0], self.screen.size[1], fillColor=self.parameters['color1'])
        self.stimulus2 = visual.Rect(self.screen, self.screen.size[0], self.screen.size[1], fillColor=self.parameters['color2'])


        self.parameters['color1'] = np.array(self.parameters['color1'])
        self.parameters['color2'] = np.array(self.parameters['color2'])

        self.stimulus1 = create_stimulus(self.screen, 
                                         self.parameters['color1'],
                                         self.parameters['color1'])
        self.stimulus2 = create_stimulus(self.screen, 
                                         self.parameters['color2'],
                                         self.parameters['color2'])

        self.stimuli = [self.stimulus1, self.stimulus2]
        self.t = 0
        self.n_frames_per_stimulus =  self.session.frame_rate / self.parameters['frequency']

        size_fixation_pix = self.session.deg2pix(self.parameters['size_fixation_deg'])

        self.fixation = visual.GratingStim(self.screen, 
                                           tex='cross', 
                                           mask='circle', 
                                           size=size_fixation_pix, 
                                           texRes=512, 
                                           color='white', 
                                           sf=0)

    def draw(self):
        self.stimuli[self.t / self.n_frames_per_stimulus % (len(self.stimuli))].draw()
        self.fixation.draw()
        self.t += 1
        super(FlickerTrial, self).draw()

    def key_event(self, key):
        super(FlickerTrial, self).key_event(key)

        if key in ['esc', 'escape', 'q']:
            self.events.append([-99,self.session.clock.getTime()-self.start_time])
            self.session.logging.info('run canceled by user')
            self.session.stop()
            self.stop()
        if key == 'z':
            #self.stimulus2.fillColor = self.stimulus2.fillColor * 0.98
            #self.parameters['color2'] *= 1./0.9
            self.parameters['color2'] += 0.05
            self.stimulus[1] =  create_stimulus(self.screen, 
                                         self.parameters['color2'],
                                         self.parameters['color2'])
            print self.stimulus2.image.mean(0).mean(0)
        if key == 'm':
            #self.stimulus2.fillColor = self.stimulus2.fillColor * 1 / 0.98
            #self.parameters['color2'] *= 0.9
            self.parameters['color2'] -= 0.05
            self.stimulus[1] =  create_stimulus(self.screen, 
                                         self.parameters['color2'],
                                         self.parameters['color2'])

            print self.stimulus2.image.mean(0).mean(0)

