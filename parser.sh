java -mx2g -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -port 9199 -loadClassifier ./classifiers/english.all.3class.distsim.crf.ser.gz &
java -mx2g -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -port 9198 -loadClassifier ./classifiers/indian-names1-ner-model.old.ser.gz &
sleep 5
python -c "import ResumeParser;ResumeParser.parseZipFiles('$1');"
# fuser -k 9198/tcp
# fuser -k 9199/tcp
lsof -i tcp:9198 | grep -v PID | awk '{print $2}' | xargs kill
lsof -i tcp:9199 | grep -v PID | awk '{print $2}' | xargs kill