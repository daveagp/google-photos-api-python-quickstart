# Use Google Photos API and Python to download or explore your photo collection

(Forked from another quickstart guide, kudos to ido-ran)

This repo allows you to

- run a Python program on your computer that connects to your Google Photos account using the Google Photos API
- and then download metadata and photos to your local machine

For example, this can be used to create an offline backup, run a screensaver on your machine, or to export your photos if you want to stop using Google Photos.

For more context, see `https://daveagp.wordpress.com/2024/04/29/google-photos-api-for-export-and-one-day-an-ubuntu-screensaver/`

## HOWTO

1. You have to create a "Google APIs & Services" application. This is using the Google Cloud Console. You don't actually need to sign up or pay for Google Cloud services itself.

2. On the "credentials" tab, create a Web application client id. Download its client secret file as json, and take the `client_secret.json` and put it in the same directory as this repo. It will contain something like `{"web":{"client_id":"61.....apps.googleusercontent.com","project_id":"name-you-chose","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"..."}}`

3. Under "Authorized redirect URIs" for your Web application, add `http://localhost:8888/`

4. On the "OAuth consent screen" tab, leave your application in testing mode (no need to "PUBLISH APP"), but add your personal gmail account as a test user.

5. The first time you use it, you'll have to use a brower to approve the app's access to your account. The Python script will output the URL you need to visit.

## APPLICATIONS

To create a slideshow of your photos, here is a nice program, and a way to caption the photos by their exif date:

`feh "/path/to/your/images/" --info "exiftool -DateTimeOriginal %F | cut -d : -f 2- | head -c 11 | sed s/:/-/g" -ZxFz -D 5`

## TROUBLESHOOTING

If you get an `invalid_grant: Token has been expired or revoked` error, try deleting the `token.pickle` file.

## TODOs

* Make `feh` into an actual screensaver that turns on when your computer detects no user activity.

* Check for duplicate photos (e.g. with different size) by looking for duplicate exif timestamps or filenames.

* Somehow deal with non-jpg things

* What's the deal with grouped multiple photos where there is a "main" one

* Exclude certain folders, e.g. archival construction of plumbing

* Don't forget to organize the wedding day photos