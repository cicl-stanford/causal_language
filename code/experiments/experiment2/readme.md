# Commands to remember

## Run expt:

1. Navigate to this directory
2. run `psiturk`
3. in psiturk terminal run `server on` and then `debug`

## Navigate to diff parts of experiment

After clicking to popup window and consent, in developer console, to navigate to diff sections, run:

* `CURRENTVIEW = new Instructions();` to get to the Instructions slide
* `CURRENTVIEW = new Comprehension();` to get to the Comprehension check slide
* `CURRENTVIEW = new TestPhase();` to get to the main section of the expt
    * while in the main section, run the following to get to the next slide:
        ~~~
        STATE.set_index(STATE.index + 1);
        tPhase.run_trial();
        ~~~
* `CURRENTVIEW = new Demographics();` to get to the demographics slide
