-- Save all properties from accountproperty as preferences in account table.
DO $$DECLARE accountproperty RECORD;
BEGIN
  FOR accountproperty IN SELECT * FROM accountproperty LOOP
    UPDATE account
      SET preferences = preferences || hstore(accountproperty.property, accountproperty.value)
      WHERE account.id = accountproperty.accountid;
  END LOOP;
END$$;
