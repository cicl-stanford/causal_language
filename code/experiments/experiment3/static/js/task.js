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
        CURRENTVIEW = new TrainingInstructions();
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

var TrainingInstructions = function() {

    // Hide all slides
    $(".slide").hide();
    // Grab the insturctions
    var slide = $("#instructions-1");


    // Instructions view count is initialized with the configuration (kind of a hack)
    // Only disable the continue button on the first instructions view
    if ($c.inst_viewed == 0) {
        $('#inst1_cont').prop('disabled', true);
    }
    $c.inst_viewed = $c.inst_viewed + 1;

    // Play video when button pressed
    $("#inst_play").click(function () {
        $("#inst_video").load();
        $("#inst_video").trigger("play");
        $("#inst_play").text("Replay");
    });

    // If not testing, enable the button after watching the video
    if ($c.testing) {
        $('#inst1_cont').prop('disabled', false);
        $("#video_check").text("(Please press continue to proceed)")
    } else {
        $("#inst_video").on('ended', function() {
            $('#inst1_cont').prop('disabled', false);
            $("#video_check").text("(Please press continue to proceed)");
        })
    }

    // Set click handler to next button in instructions slide
    $("#inst1_cont").click(function () {
        $("#inst1_cont").off();
        $("#inst_video").off();
        $("#inst_play").off();
        $("#inst_play").text("Play Video");

        $(".slide").hide();
        var slide = $("#instructions-2");
        slide.fadeIn($c.fade);
    });

    $("#inst2_cont").click(function () {
        $("#inst2_cont").off();
        $(".slide").hide();
        CURRENTVIEW = new TrainingComprehension();
    });

    // Fade in the instructions
    slide.fadeIn($c.fade);


};


var TrialInstructions = function() {

    $(".slide").hide();

    var slide = $("#instructions-3");

    $("#inst3_cont").click(function () {
        $("#inst3_cont").off();
        $(".slide").hide();
        CURRENTVIEW = new TrialComprehension();
    })

    slide.fadeIn($c.fade);
};

/*****************
 *  COMPREHENSION CHECK QUESTIONS*
 *****************/

var TrainingComprehension = function(){

    // Hide everythin else
    $(".slide").hide();

    // Show the comprehension check section
    $("#comprehension-check1").fadeIn($c.fade);

    // disable button initially
    $('#comp-cont1').prop('disabled', true);

    // set handler. On any change to the comprehension question inputs, enable 
    // the continue button if the number of responses is at least 1
    $('.compQ').change(function () {
        var q1_check = $('input[name=comprehension_radio1]:checked').length > 0
        var q2_check = $('input[name=comprehension_radio2]:checked').length > 0
        var q3_check = $('input[name=comprehension_radio3]:checked').length > 0

        if (q1_check && q2_check && q3_check) {
            $('#comp-cont1').prop('disabled', false);
        }else{
            $('#comp-cont1').prop('disabled', true);
        }
    });

    // set handler. On click of continue button, check whether the input value
    // matches the given answer. If it does, continue, otherwise to got comprehension check fail
    $('#comp-cont1').click(function () {           

       var q1_resp = $('input[name=comprehension_radio1]:checked').val();
       var q2_resp = $('input[name=comprehension_radio2]:checked').val();
       var q3_resp = $('input[name=comprehension_radio3]:checked').val();


       // correct answers 
       var q1_answer = "A_B";
       var q2_answer = "gate";
       var q3_answer = "4";

       // debug(q1_answer)
       // debug(q2_answer)



       if((q1_resp == q1_answer) && (q2_resp == q2_answer) && (q3_resp == q3_answer)){
       // if(q1_resp == q1_answer){
            CURRENTVIEW = new ComprehensionCheckPass("train");
       }else{
            $('input[name=comprehension_radio1]').prop('checked', false);
            $('input[name=comprehension_radio2]').prop('checked', false);
            $('input[name=comprehension_radio3]').prop('checked', false)
            $('#comp-cont1').off();
            $('.compQ').off();
            CURRENTVIEW = new ComprehensionCheckFail("train");
       }
    });
}


var TrialComprehension = function() {

    $(".slide").hide();


    $("#comprehension-check2").fadeIn($c.fade);

    $('#comp-cont2').prop('disabled', true);

    $('.compQ').change(function () {
        var q1_check = $('input[name=comprehension_radio4]:checked').length > 0
        var q2_check = $('input[name=comprehension_checkbox]:checked').length > 0

        if (q1_check && q2_check) {
            $('#comp-cont2').prop('disabled', false);
        } else {
            $('#comp-cont2').prop('disabled', true);
        }
    });


    $('#comp-cont2').click(function () {

        var q1_resp = $('input[name=comprehension_radio4]:checked').val();

        var q2_resp = [];
        $('input[name=comprehension_checkbox]:checked').each(function () {
            q2_resp.push($(this).val());
        });
        q2_resp = q2_resp.sort().join(',');

        var q1_answer = "2";
        var q2_answer = ["caused", "enabled"].sort().join(',');

        if((q1_resp == q1_answer) && (q2_resp == q2_answer)) {
            CURRENTVIEW = new ComprehensionCheckPass("test");
        } else {
            $('input[name=comprehension_radio4]').prop('checked', false);
            $('input[name=comprehension_checkbox]').prop('checked', false);
            $('#comp-cont2').off();
            $('.comQ').off();
            CURRENTVIEW = new ComprehensionCheckFail("test");
        }
    });
}

/*****************
* COMPREHENSION PASS SCREEN*
******************/
var ComprehensionCheckPass = function(exp_section) {
    $(".slide").hide();
    $("#comprehension_check_pass").fadeIn($c.fade);

    $("#comprehension_pass").click(function () {

        if (exp_section == "train") {
            CURRENTVIEW = new TrainPhase();
        } else if (exp_section == "test") {
            CURRENTVIEW = new TestPhase();
        }
    })
}

/*****************
 *  COMPREHENSION FAIL SCREEN*
 *****************/

var ComprehensionCheckFail = function(exp_section){
// Show the slide
$(".slide").hide();
$("#comprehension_check_fail").fadeIn($c.fade);
// $('#instructions-training').unbind();
// Don't think this does anything. There is no comprehension id
// $('#comprehension').unbind();

$('#comprehension_fail').click(function () {

        $("#comprehension_fail").off();

        if (exp_section == "train") {
            CURRENTVIEW = new TrainingInstructions();
        } else if (exp_section == "test") {
            CURRENTVIEW = new TrialInstructions();
        }

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

var verb_to_sentence = function(verb) {
    if (verb == "affected") {
        return "Ball A <b>affected</b> Ball B's going through the red exit.";
    } else if (verb == "caused") {
        return "Ball A <b>caused</b> Ball B to go through the red exit.";
    } else if (verb == "enabled") {
        return "Ball A <b>enabled</b> Ball B to go through the red exit.";
    } else {
        return "Ball A <b>made no difference</b> to Ball B's going through the red exit.";
    }
}

function coinFlip() {
    return (Math.floor(Math.random() * 2) == 1);
}


var TrainPhase = function () {
    // Initialize relevant TestPhase values
    this.traininginfo;
    this.response;

    var sentence_order = $c.sentences.map(x => x["word"])
    psiTurk.recordUnstructuredData("sentence_order", sentence_order);

    // Define the trial method which runs recursively
    this.run_training = function () {
        // If we have exhausted all the trials, transition to next phase and close down the function,
        // else if we have reached the attention check point, run the attention check
        // Otherwise run the trial
        if (STATE.training_index >= $c.training.length) {
            CURRENTVIEW = new TrialInstructions();
            return
        } else {
            // get the appropriate trial info
            this.traininginfo = $c.training[STATE.training_index];

            // update the prgoress bar. Defined in utils.js
            update_progress(STATE.training_index, $c.training.length, "train");

            // get the video name and set appropriate video formats for different types of browsers.
            // Load the video (autoplay feature is active, will start when shown see trial.html)
            video_number = this.traininginfo.training_number;
            $("#training_video_mp4").attr("src",'/static/videos/mp4/training_clip_' + video_number + '.mp4');
            $("#training_video_webm").attr("src",'/static/videos/webm/training_clip_' + video_number + '.webm');
            // $("#video_ogg").attr("src",'/static/videos/ogg/' + video_name + '.oggtheora.ogv');
            $(".stim_video").load();

            // Continue button should be initially disabled
            $cont_button = $('#training_next');
            $cont_button.prop('disabled', true);

            var play_count = 0

            // set up event handler for the video play button
            $("#training-play").click(function () {
                $(".stim_video").load();
                $('.stim_video').trigger('play');

                if ($c.testing) { 
                    play_count = play_count + 1;

                    if (play_count == 1) {
                        $(this).text("Watch Again");
                    } else if (play_count == 2) {
                        $(this).text("Replay")
                    }

                    if ($("input[name=training_response]:checked").length > 0 && play_count >= 2) {
                        $cont_button.prop("disabled", false)
                        $("#training_video_check").text("(Please press continue to proceed.)")
                    }

                } else {
                    $("#training-play").prop('disabled', true)
                }


                // Enable the play button immediately or after delay, based on how
                // many times the participant has viewed the video
                // if (play_count < 3) {

                //     if (!$c.testing) {
                //         $("#training-play").prop('disabled', true)
                //     }
                //     // Change the text after the first play
                //     // Change the text and reveal the response container after the second play
                //     if (play_count == 1) {
                //         $(this).text('Watch Again');
                //     } else if (play_count == 2) {
                //         $(this).text('Replay');
                //         // $cont_button.prop('disabled', false);
                //         if ($c.testing) {
                //             // $("#training_response_container").show()
                //             if ($("input[name=training_response]:checked").length > 0) {
                //                 $cont_button.prop("disabled", false)
                //                 $("#training_video_check").text("(Please press continue to proceed.)")
                //             }
                //         } 

                //     }
                // } else {
                //     if (!$c.testing) {
                //         $("#training-play").prop('disabled', true)
                //     }
                // }
            });

            $(".stim_video").on("ended", function () {

                play_count = play_count + 1;

                if (!$c.testing) {
                    if (play_count == 1) {
                        $("#training-play").text("Watch Again");
                    }

                    if (play_count == 2) {
                        $("#training-play").text("Replay");
                        // $("#training_response_container").show()
                        if ($("input[name=training_response]:checked").length > 0) {
                            $cont_button.prop("disabled", false)
                            $("#training_video_check").text("(Please press continue to proceed.)")
                        }

                    }   
                    $("#training-play").prop("disabled", false)
                }

            });

            html = "";
            for (var i=0; i<$c.sentences.length; i++) {
                sentence = $c.sentences[i]["sentence"];
                answer = $c.sentences[i]["word"];
                html += '<input type = "radio" name = "training_response" value = "' + answer + '" class = response_radio><div class = "response_sentence">' + sentence + '</div><br/>';
            }

            $("#training_answer_container").html(html);

            $(".response_radio").on("change", function() {
                if ($("input[name=training_response]:checked").length > 0 && play_count > 1) {
                    $cont_button.prop("disabled", false);
                    $("#training_video_check").text("(Please press continue to proceed.)")
                } else {
                    $cont_button.prop("disabled", true);
                }
            });

            // hide all displayed html
            $('.slide').hide();

            // show the trial section of the html but hide the response section
            var start = performance.now()
            $('#training').fadeIn($c.fade);
            // $('#training_response_container').hide();
            // start timer for recording how long people have watched
            // var start = performance.now();

            //save the tPhase object for use in the event handler
            train_phase = this;
            // set the event handler for the continue click
            $cont_button.on('click', function() {
                // get the answers
                var response = $("input[name = training_response]:checked").val();
                // debug(response)
                // save the response to the psiturk data object
                var response_time = performance.now() - start;

                var data = {
                    // 'id': train_phase.trialinfo.id,
                    'training_clip_number': train_phase.traininginfo.training_number,
                    // 'description': tPhase.trialinfo.description,
                    'response': response,
                    'play_count': play_count,
                    'time': response_time
                }
                psiTurk.recordTrialData(data);

                // increment the state
                // STATE.set_index(STATE.training_index + 1);
                STATE.training_index += 1
                //disable event handlers (will be re-assigned in the next trial)
                $cont_button.off();
                $('#training-play').off();
                $('#training-play').text('Play Video');
                $("#training_video_check").text("(You have to watch the video twice and select a description in order to continue.)")
                $("#training-play").prop('disabled', false);
                $(".stim_video").off();
                $(".response_radio").off();
                $("input[name=training_response]").attr("checked", false);

                train_phase.run_training();
                return
            });
        };
    };

    this.run_training()
};


var TestPhase = function () {
    // Initialize relevant TestPhase values
    this.trialinfo;
    this.response;

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
            update_progress(STATE.index, $c.trials.length, "test");

            html = "";
            for (var i=0; i<$c.sentences.length; i++) {
                sentence = $c.sentences[i]["sentence"];
                answer = $c.sentences[i]["word"];
                html += '<input type="radio" name="test_prompt" id="' + answer + '" class="prompt_radio"><div class = "response_sentence">' + sentence + '</div><br/>';
            }

            // $("#describer-selection").html(verb_to_sentence(this.trialinfo.utterance))
            $("#describer-selection").html(html);
            // $(".prompt_radio")
            // $('.prompt_radio').attr("disabled", true);
            // debug(this.trialinfo.utterance)
            $("#" + this.trialinfo.utterance).prop("checked", true);
            // get the video name and set appropriate video formats for different types of browsers.
            // Load the video (autoplay feature is active, will start when shown see trial.html)

            if (Number.isInteger(this.trialinfo.trial)) {
                var stem = "clip_"
            } else {
                var stem = "attention_check_"
            }

            flip = coinFlip()
            left_video = (flip ? this.trialinfo.clip_1 : this.trialinfo.clip_2);
            right_video = (flip ? this.trialinfo.clip_2 : this.trialinfo.clip_1);
            $("#video1_mp4").attr("src",'/static/videos/mp4/' + stem + left_video + '.mp4');
            $("#video1_webm").attr("src",'/static/videos/webm/' + stem + left_video + '.webm');
            $("#video2_mp4").attr("src",'/static/videos/mp4/' + stem + right_video + '.mp4');
            $("#video2_webm").attr("src",'/static/videos/webm/' + stem + right_video + '.webm');
            // $("#video_ogg").attr("src",'/static/videos/ogg/' + video_name + '.oggtheora.ogv');
            // $(".stim_video").load();
            $("#stim_video1").load();
            $("#stim_video2").load();


            // Continue button should be initially disabled
            $cont_button = $('#trial_next');
            $cont_button.prop('disabled', true);

            // $("#play2").prop("disabled", true);
            $("#play2").hide()


            var left_play_count = 0;
            var right_play_count = 0;


            $("#play1").click(function () {
                // $("#stim_video1").load();
                $("#stim_video1").trigger('play');

                left_play_count = left_play_count + 1;

                // Do this only on the first play
                if (left_play_count == 1) {
                    // if not testing
                    if (!$c.testing) {
                        // Hide the left play button. Show the right one after 10 seconds
                        $("#play1").hide()
                        // setTimeout(function() {$("#play2").show()}, 10000)
                    } else {
                        // if testing, no delay
                        $("#play1").hide()
                        $("#play2").show()
                    }
                    $(this).text("Replay");
                } else {
                    // On additional plays, disable the button when it is pressed (until the video ends)
                    if (!$c.testing) {
                        $("#play1").prop("disabled", true)
                        // setTimeout(function() {$("#play1").prop("disabled", false)}, 10000)
                    }
                }

            });

            $("#stim_video1").on("ended", function() {
                if (left_play_count == 1) {
                    if (!$c.testing) {
                        $("#play2").show()
                    }
                } else {
                    $("#play1").prop("disabled", false)
                }
            });


            $("#play2").click(function () {
                // $("#stim_video2").load();
                $("#stim_video2").trigger("play");

                right_play_count = right_play_count + 1;

                // Do this only on the first play
                if (right_play_count == 1) {
                    // if testing
                    if (!$c.testing) {
                        // hide the right play button
                        $("#play2").hide();
                    } else {
                        // If not testing show the right button on the response container
                        $("#play1").show()
                        $(".ui-slider-handle").hide();
                        $(".start_hidden").css('visibility', 'visible');
                    }
                    $(this).text("Replay");
                } else {
                    // On future presses disable the button for 10 seconds when pressed
                    if (!$c.testing) {
                        $("#play2").prop("disabled", true);
                        // setTimeout(function() {$("#play2").prop("disabled", false)}, 10000)
                    }
                }
            });


            $("#stim_video2").on("ended", function() {
                if (right_play_count == 1) {
                    if (!$c.testing) {
                        $("#play1").show();
                        $("#play2").show();
                        $(".ui-slider-handle").hide();
                        $(".start_hidden").css('visibility', 'visible');
                    }
                } else {
                    if (!$c.testing) {
                        $("#play2").prop("disabled", false);
                    }
                }
            });

            $(".slider").slider().on("slidestart", function( event, ui ) {
                // debug("here")
                $(this).find('.ui-slider-handle').show();
                $cont_button.prop("disabled", false);
            });

            // hide all displayed html
            $('.slide').hide();

            // show the trial section of the html but hide the response section
            var start = performance.now()
            $('#trial').fadeIn($c.fade);
            $('.start_hidden').css('visibility', 'hidden');
            // start timer for recording how long people have watched
            // var start = performance.now();

            //save the tPhase object for use in the event handler
            tPhase = this;
            // set the event handler for the continue click
            $cont_button.on('click', function() {
                // get the answers
                // var response = $("input[name = question_response]:checked").val();
                var response = $("#task_slider").slider("value");
                // debug(response)
                // save the response to the psiturk data object
                var response_time = performance.now() - start;


                var data = {
                    'trial': tPhase.trialinfo.trial,
                    'utterance': tPhase.trialinfo.utterance,
                    'response': response,
                    'left_video': left_video,
                    'right_video': right_video,
                    'left_play_count': left_play_count,
                    'right_play_count': right_play_count,
                    'time': response_time
                }
                psiTurk.recordTrialData(data);

                // increment the state
                STATE.set_index(STATE.index + 1);
                //disable event handlers (will be re-assigned in the next trial)
                $cont_button.off();
                $('#play1').off();
                $('#play1').text('Play Video');
                $('#play1').prop('disabled', false);
                $('#stim_video1').off();
                $('#play2').off();
                $('#play2').text('Play Video');
                $('#play2').prop('disabled', false);
                $('#stim_video2').off();
                // $('.slider').slider().off();
                // $(".response_radio").off();
                // $("input[name=question_response]").attr("checked", false);

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
        // CURRENTVIEW = new BotCheck();
        // CURRENTVIEW = new TrainPhase();
        // CURRENTVIEW = new TestPhase();
        CURRENTVIEW = new TrainingInstructions();
        // CURRENTVIEW = new Comprehension();
        // CURRENTVIEW = new TrialInstructions();
    } else {
        CURRENTVIEW = new TestPhase();
    }
});
