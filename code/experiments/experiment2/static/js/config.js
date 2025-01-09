/* config.js
 * 
 * This file contains the code necessary to load the configuration
 * for the experiment.
 */

// Object to hold the experiment configuration. It takes as parameters
// the numeric codes representing the experimental condition and
// whether the trials are counterbalanced.
var Config = function (condition, counterbalance) {

    // These are the condition and counterbalancing ids
    // condition is which one is first
    this.condition = condition;
    // counterbalance is whether or not to show the two at the same time
    this.counterbalance = counterbalance;

    // Whether debug information should be printed out
    this.debug = true;
    // The amount of time to fade HTML elements in/out
    this.fade = 200;
    // List of trial information object for each experiment phase
    this.trials = new Object();

    // Canvas width and height
    this.canvas_width = 300;
    this.canvas_height = 300;

    // indicator for whether instructions have been viewed
    this.inst_viewed = 0;
    // record of bot check responses
    this.check_responses = [];

    this.testing = false;

    // Lists of pages and examples for each instruction page.  We know
    // the list of pages we want to display a priori.
    // this.instructions = {
    //     pages: ["instructions-training-1", "instructions-training-2"]
    // };

    // The list of all the HTML pages that need to be loaded
    this.pages = [
        "trial.html"
    ];
    var that = this;
    // Parse the JSON object that we've requested and load it into the
    // configuration

    this.parse_config = function (data) {
        this.trials = shuffle(data["stim"])
        this.sentences = shuffle(data["sentences"].slice(0,data["sentences"].length - 1))
        this.sentences.push(data["sentences"][data["sentences"].length - 1])
    };


    // Load the experiment configuration from the server
    this.load_config = function () {
        var that = this;
        $.ajax({
            dataType: "json",
            url: "/static/json/stim.json",
            async: false,
            success: function (data) { 
                if (that.debug) {
                    console.log("Got configuration data");
                }
                that.parse_config(data);
            }
        });
    };

    // Request from the server configuration information for this run
    // of the experiment
    this.load_config();
    // Set a point to do the attention check for bots
    // this.check_point = Math.floor(this.trials.length)/2;

    // instantiate an array to keep track of 
    // this.check_responses1 = [];
    // this.check_responses2 = [];
};
