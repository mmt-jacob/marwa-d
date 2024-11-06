SET _MONGO_BIN=C:\MongoDB\bin
SET _SRC=/code/react/linq/server/src/data/json
%_MONGO_BIN%\mongoimport /jsonArray /db:linq /collection:user /file:%_SRC%/user.json
%_MONGO_BIN%\mongoimport /jsonArray /db:linq /collection:riskfactor /file:%_SRC%/riskfactor.json
%_MONGO_BIN%\mongoimport /jsonArray /db:linq /collection:facility /file:%_SRC%/facility.json
%_MONGO_BIN%\mongoimport /jsonArray /db:linq /collection:roomconfig /file:%_SRC%/roomconfig.json
