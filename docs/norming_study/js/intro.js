
const intro = {
    type: jsPsychHtmlButtonResponse,
    stimulus:
        `<h1><b>Welcome!</b></h1><div style="text-align:justify; padding:20px; max-width:900px;">
        <p>In this study we are interested in how you understand the words "caused", "enabled", and "affected". We will present you with a series of sentences where each one uses one of those words, and we will ask you to rate how "acceptable" you feel the sentence is. We are interested in your intuitions about whether the sentence sounds natural. Sentences that sound good to you should receive higher ratings and sentences that sound bad should receive lower ratings.</p>
         </div>
         <div> <p>For example, this is an example of an acceptable sentence:</p>
         <img src="images/good_sample.jpg" width="900"><br>
         <p>This is an example of a sentence that is not acceptable:</p>
         <img src="images/bad_sample.jpg" width="900"><br>
         </div>
         <div style="text-align:justify; padding:20px; max-width:900px;"><p>These examples are meant to give you an idea of what to expect, but there are no right answers. We are interested in your intuitive sense of what sounds good and what sounds bad. We will ask you to complete ratings for 66 sentences overall.</p></div>
         <div><p>When you are ready to begin press the start button below</p></div>
        <h3>Thank you for your participation!<h3>`,
    choices: ['Start']
};
