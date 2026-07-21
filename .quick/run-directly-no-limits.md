REPO (output auto → <target>/.work.soc/):
./gateway.sh -t /mnt/work/Projects/system-erp \
  --mount /mnt/work/Projects/system-erp \
  -n -m deep

URL (set output-dir to target project .work.soc):
./gateway.sh -t http://localhost:13000/ \
  -n -m deep --i-have-authorization \
  --output-dir /mnt/work/Projects/system-erp/.work.soc

Logs + reports:
<output-dir>/strix_runs/<run-name>/strix.log
<output-dir>/strix_runs/<run-name>/run.json
