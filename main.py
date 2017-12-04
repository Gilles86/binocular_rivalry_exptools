from session import CalibrateSession, IntensityThresholdSession, EquiluminanceCalibrateSession, MRIWaitSession, RDMSession
import appnope
import os
import numpy as np

def main():
    #initials = raw_input('Your initials: ')
    #run_nr = int(raw_input('Run number: '))
    #scanner = raw_input('Are you in the scanner (y/n)?: ')
    #track_eyes = raw_input('Are you recording gaze (y/n)?: ')
    #if track_eyes == 'y':
        #tracker_on = True
    #elif track_eyes == 'n':
        #tracker_on = False
        
    initials = 'GdH'
    run = 1
    appnope.nope()


    blue_intensity_fn = 'data/blue_intensity_%s.txt' % initials
    red_intensity_fn = 'data/red_intensity_%s.txt' % initials
    purple_intensity_fn = 'data/purple_intensity_%s.txt' % initials

    if not os.path.exists(blue_intensity_fn):
        blue_thr_session = IntensityThresholdSession(initials, run, (0.0, 0.0, 1.0))
        blue_thr = blue_thr_session.run()
        np.savetxt(blue_intensity_fn, [blue_thr])

    blue_intensity = np.loadtxt(blue_intensity_fn)

    if not os.path.exists(red_intensity_fn):
        red_thr_session = EquiluminanceCalibrateSession(initials, run, (0.0, 0.0, 1.0), (1.0, 0., 0.0))
        red_thr = red_thr_session.run()
        np.savetxt(red_intensity_fn, [red_thr])

    red_intensity = np.loadtxt(red_intensity_fn)

    if not os.path.exists(purple_intensity_fn):
        purple_thr_session = EquiluminanceCalibrateSession(initials, run, (0.0, 0.0, 1.0), (red_intensity, 0., blue_intensity))
        purple_thr = purple_thr_session.run()
        np.savetxt(purple_intensity_fn, [purple_thr])

    purple_intensity = np.loadtxt(purple_intensity_fn)

    block = 1
    wait = MRIWaitSession(initials, 'wait%d' % block, 'Waiting for MRI trigger')
    wait.run()
    
    while wait.quit is False:
        rdm_session = RDMSession(initials, 'run%d' % block, (0.0, 0.0, blue_intensity), (red_intensity, 0.0, 0.0), purple_intensity, simulate_mri_trigger=True, tr=4 )
        rdm_session.run()
        
        block += 1
        wait = MRIWaitSession(initials, 'wait%d' % block, 'Waiting for MRI trigger')
        wait.run()
    
    # plot_mapper_staircase(initials, run_nr)

if __name__ == '__main__':
    main()
