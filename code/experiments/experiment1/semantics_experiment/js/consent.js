// TODO: FILL OUT APPROX. EXPERIMENT LENGTH
var time = 'about 10 minutes';

const consent = {
    type: jsPsychHtmlButtonResponse,
    stimulus: '<p><b>Consent Form</b></p> <div style="text-align:left;' +
        'background-color:lightblue; padding:20px; max-width:900px;">' +
        '<p><b>Description:</b> Welcome! You are invited to participate' +
        ' in a research study in cognitive psychology. You will be asked' +
        ' to perform various tasks on a computer which may include:' +
        ' looking at images or videos, listening to sounds, reading' +
        ' scenarios, or playing games. You may be asked a number of' +
        // careful about single quotes
        " different questions about making judgments and intepreting" +
        " people's actions. All information collected will remain" +
        ' confidential. </p>' +
        ' <p> <b>Risks and benefits:</b> Risks involved in this study' +
        ' are the same as those normally associated with using a' +
        ' computer (e.g., mild eye/arm strain). If you have any pre-' +
        ' existing conditions that might make reading and completing' +
        ' a computer-based survey strenuous for you, you should' +
        ' probably elect to not participate in this study. If at any' +
        ' time during the study you feel unable to participate because' +
        ' you are experiencing strain, you may end your participation' +
        ' without penalty. We cannot and do not guarantee or promise that' +
        ' you will receive any benefits from this study. Your decision' +
        ' whether or not to participate in this study will not affect' +
        ' your employment, medical care, and/or grades in school. </p>' +
        '<p><b>Time involvement:</b> Your participation in this' +
        ' experiment will take ' + time + '. </p>' +
        '<p><b> Payment:</b> If recruitment materials indicate payment' +
        ' (e.g., Prolific or other recruitment), you will receive' +
        ' compensation as indicated. </p>' +
        "<p><b>Subject's rights:</b> If you have read this notice and" +
        ' have decided to participate in this project, please understand' +
        ' your participation is voluntary and you have the right to' +
        ' withdraw your consent or discontinue participation at any' +
        ' time without penalty or loss of benefits to which you are' +
        ' otherwise entitled. You have the right to refuse to answer' +
        ' particular questions. Your individual privacy will be' +
        ' maintained in all published and written data resulting from' +
        ' the study. </p>' +
        '<p><b>Contact information:</b> If you have any questions,' +
        ' concerns or complaints about this research study, its' +
        ' procedures, or risks and benefits, you should ask the' +
        ' Protocol Director, (Professor Tobias Gerstenberg, Phone:' +
        ' (650) 725-2431; Email: gerstenberg@stanford.edu). </p>' +
        '<p><b>Independent contact:</b> If you are not satisfied' +
        ' with how this study is being conducted, or if you have' +
        ' any concerns, complaints, or general questions about the' +
        ' research or your rights as a participant, please contact' +
        ' the Stanford Institutional Review Board (IRB) to speak' +
        ' to someone independent of the research team via email at' +
        ' irb2-manager@lists.stanford.edu, or via phone at' +
        ' (650) 723-2480 or toll free at 1-866-680-2906. You can also' +
        ' write to the Stanford IRB, Stanford University, 3000 El' +
        ' Camino Real, Five Palo Alto Square, 4th Floor, Palo Alto,' +
        ' CA 94306. </p>' +
        '<p>You may want to print a copy of this consent form to' +
        ' keep. By clicking the button below, you acknowledge that' +
        ' you have read the above information, that you are 18 years' +
        ' of age, or older and give your consent to participate in' +
        ' our internet-based study and consent for us to analyze the' +
        ' resulting data. </p> </div>' +
        '<p> Do you agree with the terms of the experiment as explained' +
        ' above? </p>',
    choices: ['I agree']
}