import logger from 'winston';
import { EMAIL_ADDRESS, EMAIL_HOST, EMAIL_PORT, EMAIL_IS_SECURE, EMAIL_USER, EMAIL_PASS } from './config';

const nodemailer = require('nodemailer');

/**
 * Send email with download link
 * @param fromName - Name of sender
 * @param subject - Email subject
 * @param toAddress - Recipient email address
 * @param link - Download link
 * @param fileName - Name of file to download
 * @param sendDate - Local date
 * @param expireDate - Link expiration date
 * @param multiple - Bool: more than one report included
 * @return - <String>
 */

const sendSMTP = async (fromName, subject, toAddress, link, fileName, sendDate, expireDate, multiple) => {

    // Read email credentials from disk
    let host = EMAIL_HOST;
    let port = EMAIL_PORT;
    let secure = EMAIL_IS_SECURE;
    let user = EMAIL_USER;
    let pass = EMAIL_PASS;
    let fromAddress = EMAIL_ADDRESS;

    // Prepare email values and messages
    sendDate = new Date(sendDate * 1000);
    let from = '"' + fromName + '" <' + fromAddress + '>';
    let textContent = createTextBody(fromName, subject, toAddress, link, fileName, sendDate, expireDate, multiple);
    let htmlContent = createHTMLBody(fromName, subject, toAddress, link, fileName, sendDate, expireDate, multiple);

    // Setup nodemailer transport
    let service;
    let transporter;
    if (host === "smtp.gmail.com") {
        transporter = nodemailer.createTransport({host, port, secure, auth: { user, pass } });
    } else if (host === "smtp.sendgrid.net") {
        service = "SendGrid";
        transporter = nodemailer.createTransport({ service, auth: { user, pass } });
    } else {
        service = "hotmail";
        transporter = nodemailer.createTransport({ service, auth: { user, pass } });
    }

    // Setup email body
    return new Promise((resolve, reject) => {
        transporter.sendMail({
                from: from,
                to: toAddress,
                subject: subject,
                text: textContent,
                html: htmlContent,
                attachments: [{
                    filename: 'VOCSN.png',
                    path: './src/resources/email_logo.png',
                    cid: 'logo@ventec.image'
                }]
            },
            function (err, info) {
                if (err) {
                    logger.info("Error: Sending email failed: " + err);
                    reject(err);
                } else {
                    if (info.messageId !== null) {
                        logger.info("Sent email to " + toAddress);
                    } else {
                        logger.info("Error: Email response was null.");
                        reject("Generated null email message.");
                    }
                    resolve(info.messageId);
                }
            }
        );
    })
};

const createTextBody = (fromName, toName, toAddress, link, fileName, sendDate, expireDate, multiple) => {
    let message = "";
    let cid = ((new Date()).getTime() / 1000).toString();
    let endDate = (expireDate.getMonth() + 1) + "/" + expireDate.getDate() + "/" + expireDate.getFullYear();
    message = "VOCSN Multi-View Reports\n\n";
    message += "Hello,\n\n";
    message += "You've received VOCSN Multi-View information from " + fromName + ".\n";
    if (multiple) {
        message += "Please use the link below to download and save the reports: \n\n";
    } else {
        message += "Please use the link below to download and save the report:\n\n";
    }
    message += link + "\n";
    message += "Note: This link will expire on " + endDate + "\n\n";
    message += "For detailed instructions about VOCSN Multi-View, see the Clinical and Technical Manual, available at https://www.venteclife.com/manual. ";
    message += "For questions, email info@venteclife.com (do not reply to this email).\n\n";
    message += "Thank you,\n";
    message += "The VOCSN Team\n";
    return message;
};

const createHTMLBody = (fromName, toName, toAddress, link, fileName, sendDate, expireDate, multiple) => {
    let message = "";
    let endDate = (expireDate.getMonth() + 1) + "/" + expireDate.getDate() + "/" + expireDate.getFullYear();
    message = "<div style='font-family: Verdana, Arial, sans-serif'>";
    message += "<p>Hello,</p>";
    message += "<p style='margin-bottom: 0'>You've received VOCSN Multi-View information from <span style='color: green'>" + fromName + ".</span></p>";
    if (multiple) {
        message += "<p style='margin-top: 0'>Please use the link below to download and save the reports: </p>";
    } else {
        message += "<p style='margin-top: 0'>Please use the link below to download and save the report: </p>";
    }
    message += '<a href="' + link + '" style="margin: auto 0 0 0px">' + fileName + '</a>';
    message += "<p style=\"margin: 0 0 auto 20px\"><i>Note: This link will expire on " + endDate + ".</i></p>";
    message += "<p style='margin-bottom: 0px'>For detailed instructions about VOCSN Multi-View, see the <i>Clinical and Technical Manual,</i> available at <a href=\"https://www.venteclife.com/VOCSNManual\" style=\"margin: 0\">VentecLife.com/VOCSNManual</a>. For questions, email <a href=\"mailto:info@venteclife.com\" style=\"margin: 0\">info@venteclife.com</a> (do not reply to this email).</p>";
    message += "<p style='margin-bottom: 0'>Thank you,</p>";
    message += "<p style='margin-top: 0'><i>The VOCSN Team</i></p></br>";
    message += '<img src="cid:logo@ventec.image" alt="VOCSN Multi-View" width="306" height="120"/>';
    message += "</div>";
    return message;
};

export { sendSMTP };