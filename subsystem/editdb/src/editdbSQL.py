import psycopg

UPDATE_ENTRY = 'update_entry'

def executeSQL(sqllist):
    error = None
    connection = psycopg.connect(dsn="host=localhost user=manage \
                                 dbname=manage password=eganam")
    database = connection.cursor()
    for sql in sqllist:
        database.execute(sql)
    connection.commit()
    connection.close()
    return error 

def addEntryBulk(data,table):
    sqllist = []
    for row in data:
        sql = 'INSERT INTO ' + table + ' ('
        first = True
        for field,value in row:
            if len(value):
                if not first:
                    sql += ','
                sql += field
                first = False
        sql += ') VALUES ('
        first = True
        for field,value in row:
            if len(value):    
                if not first:
                    sql += ','
                sql += "'" + value + "'"
                first = False
        sql += ')'
        sqllist.append(sql)
    executeSQL(sqllist)

def addEntry(req,templatebox,table):
    sql = 'INSERT INTO ' + table + ' ('
    first = True
    for field,descr in templatebox.fields.items():
        if len(req.form[field]):
            if not first:
                sql += ','
            sql += field
            first = False
    sql += ') VALUES ('
    first = True
    for field,descr in templatebox.fields.items():
        if len(req.form[field]):    
            if not first:
                sql += ','
            sql += "'" + req.form[field] + "'"
            first = False
    sql += ')'
    sqllist = [sql]
    error = executeSQL(sqllist)
    return error

def deleteEntry(selected,table,idfield):
    sql = 'DELETE FROM ' + table + ' WHERE '
    first = True
    for id in selected:
        if not first:
            sql += ' OR '
        sql += idfield + "='" + id + "'"
        first = False
    sqllist = [sql]
    error = executeSQL(sqllist)
    return error

def updateEntry(req,templatebox,table,idfield):
    sqllist = []
    data = []
  
    if type(req.form[idfield]) is list:
        for i in range(0,len(req.form[idfield])):
            values = {}
            for field,descr in templatebox.fields.items():
                if len(req.form[field][i]):
                    values[field] = req.form[field][i]
            # the hidden element UPDATE_ENTRY contains the original ID
            data.append((req.form[UPDATE_ENTRY][i],values))
    else:
        values = {}
        for field,descr in templatebox.fields.items():
            if len(req.form[field]):
                values[field] = req.form[field]
        # the hidden element UPDATE_ENTRY contains the original ID
        data.append((req.form[UPDATE_ENTRY],values))

    for i in range(0,len(data)):
        sql = 'UPDATE ' + table + ' SET '
        id,fields = data[i]
        first = True
        for field,value in fields.items():
            if not first:
                sql += ','
            sql += field + ' = ' + "'" + value + "'" 
            first = False
        sql += ' WHERE ' + idfield + "='" + id + "'"
        sqllist.append(sql)

    error = executeSQL(sqllist)
 
    # Make a list of id's. If error is returned then the original
    # id's are still valid, if (not error) then id's might have changed
    idlist = []
    if error:
        for i in range(0,len(data)):
            id,fields = data[i]
            idlist.append(id)
    else:
        if type(req.form[idfield]) is list:
            for i in range(0,len(req.form[idfield])):
                idlist.append(req.form[idfield][i])
        else:
            idlist.append(req.form[idfield])
 
    return (error,idlist)


