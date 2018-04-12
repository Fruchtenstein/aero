sqlite3 aerobia.db "ALTER TABLE wlog ADD COLUMN wplan REAL"
for r in $(sqlite3 aerobia.db 'select runnerid from runners;'); do PLAN=$(sqlite3 aerobia.db "select goal from runners where runnerid=$r"); WPLAN=$(echo "scale=6; $PLAN/52"|bc); echo $r:$PLAN:$WPLAN; for w in {1..52}; do sqlite3 aerobia.db "INSERT OR IGNORE INTO wlog (runnerid, week, wplan) VALUES ($r, $w, $WPLAN); UPDATE wlog SET wplan=$WPLAN WHERE runnerid=$r AND week=$w"; done; done
sqlite3 aerobia.db "delete from wlog where runnerid=41867 and week<6"
