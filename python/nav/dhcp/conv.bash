while read -r line; do
    date -d "$line" --iso-8601=ns
done < <(awk '/[0-9]+-[0-9]+-[0-9]+/ { gsub(/^[ ]*"/,"",$0); gsub(/"[ ]*$/,"",$0); print $0 }')
