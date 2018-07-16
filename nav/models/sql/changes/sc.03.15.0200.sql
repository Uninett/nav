-- force reset of all poll times due to problems mentioned in LP#1301343
DELETE FROM netboxinfo WHERE key='poll_times';
