let email_verify = false;
let date_email = '';
let code_email = 0;

document.getElementById('verify_email').addEventListener('click', async function () {
    document.getElementById('verify_email').style.display = 'none';
    const rawResponse = await fetch('/verify/', {
        method: 'POST',
        body: JSON.stringify({'type': 'email', 'email': document.getElementsByName('email')[1].value})
    });
    const content = await rawResponse.json();
    document.getElementById('verify_email').style.display = 'block';
    date_email = content.time;
    code_email = content.code;
    document.getElementById('input_email_verify').style.display = 'grid';
});

document.getElementsByName('email')[1].addEventListener('input', () => {
    email_verify = false;
    code_email = 0;
    document.getElementById('submit_btn').disabled = true;
});

let otp_email = document.getElementById('otp_email');
otp_email.addEventListener('input', () => {
    const date = new Date(new Date(date_email).getTime() + 10 * 60 * 1000 + 5 * 60 * 60 * 1000);
    const isNotMuchGreater = new Date() <= date;
    if (otp_email.value.length === 4 && code_email === parseInt(otp_email.value) && code_email !== 0) {
        if (isNotMuchGreater) {
            alert('Verified Successfully');
            document.getElementById('input_email_verify').style.display = 'none';
            // document.getElementsByName("email")[1].disabled = true;
            document.getElementById('verify_email').style.display = 'none';
            email_verify = true;
            if (email_verify) {
                document.getElementById('submit_btn').disabled = false;
            }
        } else {
            alert("Invalid OTP. Generate New OTP")
        }
    } else if (otp_email.value.length === 4) {
        alert('Invalid code');
    }
});
