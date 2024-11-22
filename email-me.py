# Import required packages
import smtplib
from indigo import to_email_final

# Establish connection to Gmail --

# For a gmail connection set up SMTP for gmail
server = smtplib.SMTP('smtp.gmail.com', 587)
# Connect to email server
server.ehlo()
# Encrypt connection
server.starttls()
# Establish encrypted connection
server.ehlo()

# Log into email
server.login('**REDACTED-email-from**', '**REDACTED-password-email-from**')

# Create email to send --

# Email subject
subject = 'Book on sale'
# Enter price table
body = to_email_final
# Craft email
msg = f"Subject: {subject}\n\n{body}"

# Send the email --

server.sendmail(
    '**REDACTED-email-from**',
    '**REDACTED-email-to**',
    msg
)

# Close connection to server
server.quit()