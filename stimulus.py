from psychopy import visual, core, event  # import some libraries from PsychoPy
from copy import deepcopy, copy
from psychopy.visual.basevisual import BaseVisualStim
import numpy as np

#def create_stimulus(win, color1, color2, blocksize, height, n_blocks, shift=0):

    #block1 = np.ones((blocksize, height, 3)) * color1
    #block2 = np.ones((blocksize, height, 3)) * color2


    #block = np.tile(np.concatenate([block1, block2], 1), (1, n_blocks, 1))
    #print(block.shape)

    #print(shift)

    #if shift != 0:
        #shift_pix = int((shift / 360.) * blocksize)
        #block = np.roll(block, shift_pix)
        #print block[0]

    #return visual.ImageStim(win, block, size=(blocksize*n_blocks, height), units='pix', colorSpace='rgb')

def create_stimulus(win, color1=(1, 0,0), color2=(0,0,1), stimulus_size=800, image_size=800, n_blocks=18, aperture=100, phase=0):

    stimulus = np.zeros((image_size, image_size, 3))
    
    x, y = np.meshgrid(np.arange(image_size) - image_size/2, np.arange(image_size)  - image_size/2)
    
    mask = (np.sqrt((x**2+y**2)) < image_size/2) & (np.sqrt((x**2+y**2)) > aperture)
    
    rad = np.arctan2(y, x) / np.pi / 2 + .5
    
    tmp = (np.floor((rad * n_blocks + phase/180.)) % 2).astype(bool)
    
    stimulus[mask, :] = tmp[mask][:, np.newaxis]
    
    stimulus[mask & tmp] = color1
    stimulus[mask & ~tmp] = color2
    
    return visual.ImageStim(win, stimulus, size=(stimulus_size, stimulus_size), units='pix', colorSpace='rgb')

class RDMStimulus(BaseVisualStim):

    def __init__(self,
                 win,
                 stimArray,
                 method='ML', # Pilly & Seitz, 2009
                 nFrames=3,  
                 fieldShape='circle',
                 direction=0,
                 speed=60,
                 coherence=.5):

        self.frame = 0
        self.nFrames = nFrames

        self.fieldSize = stimArray.fieldSize
        self.fieldShape = stimArray.fieldShape
        self.nDots = stimArray.nElements
        self.coherence = coherence
        self.speed = speed

        direction_rad = direction / 180 * np.pi
        self.directionVector = np.array([[np.cos(direction_rad), 
                                          np.sin(direction_rad)]])

        if method == 'ML':
            self.stimuli = []
            for range in xrange(3):
                self.stimuli.append(copy(stimArray))
                self.stimuli[-1].xys = self._newDotsXY(self.nDots)
        else:
            raise NotImplementedError('Method %s is not implemented' % method)


    def _newDotsXY(self, nDots):
        """Returns a uniform spread of dots, according to the
        fieldShape and fieldSize
        usage::
            dots = self._newDots(nDots)
        """
        # make more dots than we need and only use those within the circle
        if self.fieldShape == 'circle':
            while True:
                # repeat until we have enough; fetch twice as many as needed
                new = np.random.uniform(-1, 1, [nDots * 2, 2])
                inCircle = (np.hypot(new[:, 0], new[:, 1]) < 1)
                if sum(inCircle) >= nDots:
                    return new[inCircle, :][:nDots, :] * self.fieldSize * 0.5
        else:
            return np.random.uniform(-0.5*self.fieldSize[0],
                                        0.5*self.fieldSize[1], [nDots, 2])

    def _updateDots(self, frame):
        #new_xys = self.stimuli[frame].xys + self.directionVector * self.speed
        #self.stimuli[frame].xys = new_xys

        newPositions = self.stimuli[frame].xys + self.directionVector * self.speed
        incoherentDots = np.random.rand(self.nDots) > self.coherence

        outsideDots = ((newPositions/self.fieldSize*2)**2).sum(1) > 1
        resampledDots = np.array(np.where((incoherentDots + outsideDots)))
        #print resampledDots.size

        newPositions[resampledDots] = self._newDotsXY(resampledDots.size)
        self.stimuli[frame].xys = newPositions
        #self.stimuli[frame].xys[:self.nDots/2] = self._newDotsXY(self.nDots/2)
        self.stimuli[frame]._updateVertices()


    def draw(self):

        #if update:
            #self._updateDots(self.frame)

        self._updateDots(self.frame)
        self.stimuli[self.frame].draw()

        self.frame = (self.frame + 1) % self.nFrames

