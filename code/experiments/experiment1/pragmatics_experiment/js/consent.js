const time = '3-5 minutes';

const consent = {
    type: jsPsychHtmlButtonResponse,
    stimulus: `
    <p><b>Consent Form</b></p>
    <div style="text-align:left; vertical-align:text-top;
       background-color:lightblue; padding:20px; max-width:900px;">
       <p><b>Description:</b> Welcome! Thank you for agreeing to take 
        part in this study. We appreciate your time and effort. In this 
        study, we will present you with a series of sentences and ask you
        judge how natural they sound to you. The questions have no right or
        wrong answers--we&apos;re just exploring features of human
        psychology in this research.
       </p>
       <p> <b>Risks and benefits:</b> There are no risks associated with this study.  No benefits may reasonably be expected to result from this study. We cannot and do not guarantee or promise that you will receive any benefits from this study.</p>
       <p><b>Confidentiality:</b> Your information and/or specimens will not be used or distributed for future research studies even if all identifying information is removed.
       </p>
       <p><b>Time involvement:</b> Your involvement should take 5 to 10 minutes. 
       </p>
       <p><b> Payment:</b>You will be paid $2.00 for your time and efforts. 
       </p>
       <p><b>Subject's rights:</b> If you have read this form and have decided to participate in this project, please understand your participation is voluntary and you have the right to withdraw your consent or discontinue participation at any time without penalty or loss of benefits to which you are otherwise entitled.  The alternative is not to participate. Your individual privacy will be maintained in all published and written data resulting from the study.  No personally identifying information is ever revealed to the researchers.
       </p>
       <p><b>Contact information:</b> If you have any questions, concerns or complaints about this research, its procedures, risks and benefits, contact the Protocol Director, Ari Beller, at abeller@stanford.edu. If you are not satisfied with how this study is being conducted, or if you have any concerns, complaints, or general questions about the research or your rights as a participant, please contact the Stanford Institutional Review Board (IRB) to speak to someone independent of the research team at (650) 723-2480 or toll free at 1-866-680-2906.  You can also write to the Stanford IRB, Stanford University, 1705 El Camino Real, Palo Alto, CA 94306 or contact the IRB by email at irbnonmed@stanford.edu
       <br>
       </p>
       <p>If you consent to take part in this survey, please indicate so below.
       </p>
    </div>
    <p> Do you agree with the terms of the experiment as explained above? 
    </p>
    `,
    choices: ['I agree'],
};
