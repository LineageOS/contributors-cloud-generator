# LineageOS contributors cloud generator

To build the jar, run the following:

    cd source/
    mvn package
    cp target/contributors-cloud-generator-1.0.jar ../lib/

If you make changes in `source/`, this will need to be re-built

To generate the code, open a linux console and type:

    ./generate_wordcloud.py

This will fetch all LineageOS repos (around 110Gb), parse the commits
logs, mix the data and generate a cloud.zip in the output
folder. This will take look long time the first time.

The file resources/well-known-accounts.txt was left willfully empty. The
format of this file should match the name of the account and the list
of known emails for the account

    Name on Gerrit|nick|email1|email2|...

This project is based in a modified version of the
[kumo](https://github.com/kennycason/kumo) library.

Copyright © 2017 The LineageOS Project
