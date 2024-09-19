const demographic_form = {
    type: jsPsychSurveyHtmlForm,
    data: {
        "page_type": "participant_survey",
    },
    html: '<div style="max-width:700px; text-align:center;"> <p>' +
        'What factors influenced how you decided to respond? Do you' +
        ' have any questions or comments regarding the experiment?' +
        '</p> <textarea name="feedback" cols="40" rows="6"' +
        ' "autofocus"></textarea><p> Please provide the following' +
        ' information to complete the study. </p> <div style="text-' +
        'align:center;"> <div style="text-align:left; display:' +
        'inline-block; margin-right:20px; line-height:1.8em;"> <ol>' +
            '<li>Age:</li> <br>' +
            '<li>Gender:</li> <br><br>' +
            '<li>Race:</li> <br><br><br><br><br><br>' +
            '<li>Ethnicity:</li>' +
        '</ol> </div>' +
        '<div style="text-align:left; display: inline-block;' +
        ' line-height:1.8em;">' +
            // age text box
            '<input name="age" type="number"  min="18" max="100" /> <br> <br>' +
            // gender options
            '<input name="gender" type="radio" id="female" value=' +
                '"Female" /> <label for="female"> Female </label>' +
            '<input name="gender" type="radio" id="male" value=' +
                '"Male" /> <label for="male"> Male </label>' +
            '<input name="gender" type="radio" id="nonbinary" value=' +
                '"Non-binary" /> <label for="nonbinary"> Non-binary </label> <br>' +
            '<input name="gender" type="radio" id="other_gender" value=' +
                '"other_gender" /> <label for="other_gender"> Other: <input' +
                ' type="text" name="other_gender" /> </label> <br><br>' +
            // race options
            '<input name="race" type="radio" id="white" value=' +
                '"White" /> <label for="white"> White </label> <br>' +
            '<input name="race" type="radio" id="black" value=' +
                '"Black/African American" /> <label for="black">' +
                ' Black/African American </label> <br>' +
            '<input name="race" type="radio" id="am_ind" value=' +
                '"American Indian/Alaska Native" /> <label for="am_ind">' +
                ' American Indian/Alaska Native </label> <br>' +
            '<input name="race" type="radio" id="asian" value=' +
                '"Asian" /> <label for="asian"> Asian </label> <br>' +
            '<input name="race" type="radio" id="pac_isl" value=' +
                '"Native Hawaiian/Pacific Islander" /> <label for="pac_isl">' +
                ' Native Hawaiian/Pacific Islander </label> <br>' +
            '<input name="race" type="radio" id="other_race" value="other_race" />' +
                '<label for="other_race"> Other: <input type="text"' +
                'name="other_race" /> </label> <br><br>' +
            // ethnicity options
            '<input name="ethnicity" type="radio" id="hisp" value=' +
                '"Hispanic" /> <label for="hisp"> Hispanic </label>' +
            '<input name="ethnicity" type="radio" id="nonhisp" value=' +
                '"Non-Hispanic" /> <label for="nonhisp"> Non-Hispanic' +
                ' </label>' +
        '</div> </div>' +
        '<p> Please press the finish button to complete the experiment. </p> </div>',
    button_label: 'Finish',
    // on_start: function() { jsPsych.setProgressBar(0.96); },
    // on_finish: function() { jsPsych.setProgressBar(1.0); }
};
