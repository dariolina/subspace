OUTPUT_FOLDER=output

for LABEL in psuu
do
    rm -rf $OUTPUT_FOLDER/$LABEL*
    python -m cProfile -o $OUTPUT_FOLDER/$LABEL.pstats run_$LABEL.py >> $OUTPUT_FOLDER/$LABEL.txt
    gprof2dot --colour-nodes-by-selftime -f pstats $OUTPUT_FOLDER/$LABEL.pstats | \
        dot -Tpng -o $OUTPUT_FOLDER/$LABEL.png
done