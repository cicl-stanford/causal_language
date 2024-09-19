/* task.js
 * 
 * This file holds the main experiment code.
 * 
 * Requires:
 *   config.js
 *   psiturk.js
 *   utils.js
 */

// Create and initialize the experiment configuration object
var $c = new Config(condition, counterbalance);

// Initalize psiturk object
var psiTurk = new PsiTurk(uniqueId, adServerLoc);

// Preload the HTML template pages that we need for the experiment
psiTurk.preloadPages($c.pages);

// Objects to keep track of the current phase and state
var CURRENTVIEW;
var STATE;


/************************
* BOT CHECK
*************************/

var BotCheck = function () {
    $(".slide").hide();

    // Initialize a challenge choice value
    var challenge_choice = Math.floor(Math.random() * 6) + 1;

    // Text for image html
    var image_html = '<img id="challenge_img" src="static/images/bot_questions/challenge' + challenge_choice + '.png"">';

    var check_against = ["freddie", "gina", "mohammed", "juan", "elise", "kayla"]

    $("#challenge_container").html(image_html);
    $("#bot_check_button").prop("disabled", true);

    $("#bot_text").on("keyup", function () {
        if ($("#bot_text").val().length != 0) {
            $("#bot_check_button").prop("disabled", false);
        } else {
            $("#bot_check_button").prop("disabled", true);
        }
    });

    $("#bot_check_button").click(function () {
        var resp = $("#bot_text").val().toLowerCase().trim();
        $c.check_responses.push(resp);


        // Reset textarea and event handlers
        $("#bot_text").val("");
        $("#bot_text").off()
        $("#bot_check_button").off()

        if (resp == check_against[challenge_choice - 1]) {
            // Upon success, record the persons responses
            // May want to record as we go? But I guess if the bot is endlessly failing the check
            // then we just won't get their data at the end?
            psiTurk.recordUnstructuredData("botcheck_responses", $c.check_responses);
            CURRENTVIEW = BotCheckSuccess();
        } else {
            CURRENTVIEW = new BotCheckFail();
        }
    });

    $("#botcheck").fadeIn($c.fade);
}

var BotCheckSuccess = function() {
    $(".slide").hide();

    $("#botcheck_pass_button").click(function () {
        CURRENTVIEW = new Instructions();
    })

    $("#botcheck_pass").fadeIn($c.fade);
}

var BotCheckFail = function(){
// Show the slide
$(".slide").hide();
$("#botcheck_fail").fadeIn($c.fade);

$('#botcheck_fail_button').click(function () {  
  $('#botcheck_fail_button').unbind();         
    CURRENTVIEW = new BotCheck();
   });
}

/*************************
 * INSTRUCTIONS         
 *************************/

var Instructions = function() {
    // Enforce condition for testing
    // $c.condition = 0
    // debug($c.condition)

    // Hide all slides
    $(".slide").hide();
    // Grab the insturctions
    var slide = $("#instructions-training");


    // Instructions view count is initialized with the configuration (kind of a hack)
    // Only disable the continue button on the first instructions view
    if ($c.inst_viewed == 0) {
        $('#inst_cont').prop('disabled', true);
    }
    $c.inst_viewed = $c.inst_viewed + 1;

    html = "";
    for (var i=0; i<$c.sentences.length; i++) {
        sentence = $c.sentences[i]["sentence"];
        html += "<li>" + sentence + "</li>";
    }

    $("#instructions_list").html(html);

    // Fade in the instructions
    slide.fadeIn($c.fade);

    $("#inst_play").click(function () {
        $("#inst_video").load();
        $("#inst_video").trigger("play");
        $("#inst_play").text("Replay");
        $("#video_check").hide();
        if ($c.testing) {
            $('#inst_cont').prop('disabled', false);
        } else {
            setTimeout(function () {$('#inst_cont').prop('disabled', false)}, 10000);
        }
    });

    // Set click handler to next button in instructions slide
    $("#inst_cont").click(function () {
        // CURRENTVIEW = new TestPhase();
        // CURRENTVIEW = new Demographics();
        $("#inst_cont").off();
        $("#inst_video").off();
        $("#inst_play").off();
        $("#inst_play").text("Play Video");
        CURRENTVIEW = new Comprehension();
    });
};

/*****************
 *  COMPREHENSION CHECK QUESTIONS*
 *****************/

var Comprehension = function(){

    // Hide everythin else
    $(".slide").hide();

    // Show the comprehension check section
    $("#comprehension-check").fadeIn($c.fade);

    // disable button initially
    $('#comp-cont').prop('disabled', true);

    // set handler. On any change to the comprehension question inputs, enable 
    // the continue button if the number of responses is at least 1
    $('.compQ').change(function () {
        var q1_check = $('input[name=comprehension_checkbox]:checked').length > 0
        // var q2_check = $('input[name=comprehension_radio]:checked').length > 0
        // if (q1_check && q2_check) {
        if (q1_check) {
            $('#comp-cont').prop('disabled', false);
        }else{
            $('#comp-cont').prop('disabled', true);
        }
    });

    // set handler. On click of continue button, check whether the input value
    // matches the given answer. If it does, continue, otherwise to got comprehension check fail
    $('#comp-cont').click(function () {           
       // var q1 = $('input[name=comprehension]:checked').val();
       var q1_resp = [];
       $('input[name=comprehension_checkbox]:checked').each(function () {
        q1_resp.push($(this).val());
       });
       q1_resp = q1_resp.sort().join(',');

       // correct answers 
       var q1_answer = ["box", "greyB", "blue", "redexit"].sort().join(',');

       // var q2_resp = $('input[name=comprehension_radio]:checked').val();
       // var q2_answer = "A";


       // if(q1_resp == q1_answer && q2_resp == q2_answer){
       if(q1_resp == q1_answer){
            CURRENTVIEW = new ComprehensionCheckPass();
       }else{
            $('input[name=comprehension_checkbox]').prop('checked', false);
            $('input[name=comprehension_radio]').prop('checked', false);
            $('#comp-cont').off();
            $('.compQ').off();
            CURRENTVIEW = new ComprehensionCheckFail();
       }
    });
}

/*****************
* COMPREHENSION PASS SCREEN*
******************/
var ComprehensionCheckPass = function() {
    $(".slide").hide();
    $("#comprehension_check_pass").fadeIn($c.fade);

    $("#comprehension_pass").click(function () {
        CURRENTVIEW = new TestPhase();
    })
}

/*****************
 *  COMPREHENSION FAIL SCREEN*
 *****************/

var ComprehensionCheckFail = function(){
// Show the slide
$(".slide").hide();
$("#comprehension_check_fail").fadeIn($c.fade);
$('#instructions-training').unbind();
// Don't think this does anything. There is no comprehension id
// $('#comprehension').unbind();

$('#comprehension_fail').click(function () {           
  CURRENTVIEW = new Instructions();
  $('#comprehension_fail').unbind();
   });
}

/*****************
 *  TRIALS       *
 *****************/

var EnableContinue = function () {
    var words = $("#text_answer").val();
    var word_count = words.trim().split(/\s+/).length;
    $("#word_count").text(word_count.toString() + "/3");
    if ((word_count > 0) && (word_count < 4) && ($("#drop_answers").val() != 0)) {
        $("#trial_next").prop('disabled', false);
        $("#word_count").css("color", "green");
    } else {
        $("#trial_next").prop('disabled', true);
        $("#word_count").css("color", "red")
    }
}

var NotEmpty = function (s) {
    return s != "";
}

var TestPhase = function () {
    // Initialize relevant TestPhase values
    this.trialinfo;
    this.response;

    var sentence_order = $c.sentences.map(x => x["word"])
    psiTurk.recordUnstructuredData("sentence_order", sentence_order);


    // Define the trial method which runs recursively
    this.run_trial = function () {
        // If we have exhausted all the trials, transition to next phase and close down the function,
        // else if we have reached the attention check point, run the attention check
        // Otherwise run the trial
        if (STATE.index >= $c.trials.length) {
            CURRENTVIEW = new Demographics();
            return
        } else {
            // get the appropriate trial info
            this.trialinfo = $c.trials[STATE.index];

            // update the prgoress bar. Defined in utils.js
            update_progress(STATE.index, $c.trials.length);

            // get the video name and set appropriate video formats for different types of browsers.
            // Load the video (autoplay feature is active, will start when shown see trial.html)
            video_name = this.trialinfo.name;
            $("#video_mp4").attr("src",'/static/videos/mp4/' + video_name + '.mp4');
            $("#video_webm").attr("src",'/static/videos/webm/' + video_name + '.webm');
            // $("#video_ogg").attr("src",'/static/videos/ogg/' + video_name + '.oggtheora.ogv');
            $(".stim_video").load();

            // Continue button should be initially disabled
            $cont_button = $('#trial_next');
            $cont_button.prop('disabled', true);

            var play_count = 0

            // set up event handler for the video play button
            $("#play").click(function () {
                $(".stim_video").load();
                $('.stim_video').trigger('play');
                play_count = play_count + 1;

                $("#play").prop('disabled', true);

                // Enable the play button immediately or after delay, based on how
                // many times the participant has viewed the video
                if (play_count < 3) {
                    if ($c.testing) {
                        $("#play").prop('disabled', false)
                    } else {
                        setTimeout(function() {$("#play").prop('disabled', false)}, 10000);
                    }
                    // Change the text after the first play
                    // Change the text and reveal the response container after the second play
                    if (play_count == 1) {
                        $(this).text('Watch Again');
                    } else if (play_count == 2) {
                        $(this).text('Replay');
                        // $cont_button.prop('disabled', false);
                        if ($c.testing) {
                            $("#response_container").show()
                        } else {
                            setTimeout(function() {$("#response_container").show()}, 10000);
                        }
                    }
                } else {
                    $("#play").prop("disabled", false);
                }
            });

            html = "";
            for (var i=0; i<$c.sentences.length; i++) {
                sentence = $c.sentences[i]["sentence"];
                answer = $c.sentences[i]["word"];
                html += '<input type = "radio" name = "question_response" value = "' + answer + '" class = response_radio><div class = "response_sentence">' + sentence + '</div><br/>';
            }

            $("#answer_container").html(html);

            $(".response_radio").on("change", function() {
                if ($("input[name=question_response]:checked").length > 0) {
                    $cont_button.prop("disabled", false);
                } else {
                    $cont_button.prop("disabled", true);
                }
            });

            // hide all displayed html
            $('.slide').hide();

            // show the trial section of the html but hide the response section
            var start = performance.now()
            $('#trial').fadeIn($c.fade);
            $('#response_container').hide();
            // start timer for recording how long people have watched
            // var start = performance.now();

            //save the tPhase object for use in the event handler
            tPhase = this;
            // set the event handler for the continue click
            $cont_button.on('click', function() {
                // get the answers
                var response = $("input[name = question_response]:checked").val();
                debug(response)
                // save the response to the psiturk data object
                var response_time = performance.now() - start;

                var data = {
                    'id': tPhase.trialinfo.id,
                    'name': tPhase.trialinfo.name,
                    'description': tPhase.trialinfo.description,
                    'response': response,
                    'play_count': play_count,
                    'time': response_time
                }
                psiTurk.recordTrialData(data);

                // increment the state
                STATE.set_index(STATE.index + 1);
                //disable event handlers (will be re-assigned in the next trial)
                $cont_button.off();
                $('#play').off();
                $('#play').text('Play Video');
                $(".response_radio").off();
                $("input[name=question_response]").attr("checked", false);

                tPhase.run_trial();
                return
            });
        };
    };

    this.run_trial()
};

/*****************
 *  DEMOGRAPHICS*
 *****************/

// Make demographic field entry and prefer not to say mutually exclusive
var OnOff = function(demo_type) {
    // If you click the NA button, empty the field
    $('#' + demo_type + '_na').click(function() {
        $('#' + demo_type + '_answer').val(""); 
    });

    // If you enter text into the field entry, uncheck prefer not to say
    $('#' + demo_type + '_answer').on('keyup', function() {
        if ($('#' + demo_type + '_answer').val() != "") {
            $('#' + demo_type + '_na').prop('checked', false);
        }
    });
} 

var Demographics = function(){

    var that = this; 

    // Show the slide
    $(".slide").hide();
    $("#demographics").fadeIn($c.fade);

    //disable button initially
    $('#trial_finish').prop('disabled', true);

    //checks whether all questions were answered
    $('.demoQ').change(function () {
        var lang_check = $('input[name=language]').val() != "" || $('input[name=language]:checked').length > 0
        var age_check = $('input[name=age]').val() != "" || $('input[name=age]:checked').length > 0
        var gen_check = $('input[name=gender]').val() != "" || $('input[name=gender]:checked').length > 0
        var race_check = $('input[name=race]').val() != "" || $('input[name=race]:checked').length > 0
        var eth_check = $('input[name=ethnicity]:checked').length > 0
        if (lang_check && age_check && gen_check && race_check && eth_check) {
            $('#trial_finish').prop('disabled', false)
        } else {
            $('#trial_finish').prop('disabled', true)
        }
    });
    
    // Make the field entries turn off if prefer not to say is checkd
    // (and vice versa)
    OnOff('language')
    OnOff('age')
    OnOff('gender')
    OnOff('race')

    this.finish = function() {

        // Show a page saying that the HIT is resubmitting, and
        // show the error page again if it times out or error
        var resubmit = function() {
            $(".slide").hide();
            $("#resubmit_slide").fadeIn($c.fade);

            var reprompt = setTimeout(prompt_resubmit, 10000);
            psiTurk.saveData({
                success: function() {
                    clearInterval(reprompt); 
                    finish();
                }, 
                error: prompt_resubmit
            });
        };

        // Prompt them to resubmit the HIT, because it failed the first time
        var prompt_resubmit = function() {
            $("#resubmit_slide").click(resubmit);
            $(".slide").hide();
            $("#submit_error_slide").fadeIn($c.fade);
        };

        // Render a page saying it's submitting
        psiTurk.preloadPages(["submit.html"])
        psiTurk.showPage("submit.html") ;
        psiTurk.saveData({
            success: psiTurk.completeHIT, 
            error: prompt_resubmit
        });
    }; //this.finish function end 

    $('#trial_finish').click(function () {           
       var feedback = $('textarea[name = feedback]').val();
       var language = $('input[name=language]').val();
       var age = $('input[name=age]').val();
       var gender = $('input[name=gender]').val();
       var race = $('input[name=race]').val();
       var ethnicity = $('input[name=ethnicity]:checked').val();

       psiTurk.recordUnstructuredData('feedback',feedback);
       psiTurk.recordUnstructuredData('language',language);
       psiTurk.recordUnstructuredData('age',age);
       psiTurk.recordUnstructuredData('gender',gender);
       psiTurk.recordUnstructuredData('race',race);
       psiTurk.recordUnstructuredData('ethnicity', ethnicity)
       that.finish();
   });
};


// --------------------------------------------------------------------
// --------------------------------------------------------------------

/*******************
 * Run Task
 ******************/

$(document).ready(function() { 
    // Load the HTML for the trials
    psiTurk.showPage("trial.html");

    // Record various unstructured data
    psiTurk.recordUnstructuredData("condition", condition);
    psiTurk.recordUnstructuredData("counterbalance", counterbalance);
    // Record the order in which the frames are presented.
    // 1 = shortest frame, 2 = mid length, 3 = longest
   // psiTurk.recordUnstructuredData("choices", $("#choices").html());

    // Start the experiment
    STATE = new State();
    // $c.testing = true;
    // Begin the experiment phase
    if (STATE.instructions) {
        // CURRENTVIEW = new Demographics();
        CURRENTVIEW = new BotCheck();
        // CURRENTVIEW = new TestPhase();
        // CURRENTVIEW = new Instructions();
    } else {
        CURRENTVIEW = new TestPhase();
    }
});
