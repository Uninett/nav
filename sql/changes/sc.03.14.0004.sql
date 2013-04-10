-- Create table for netbios names

CREATE TABLE image (
  imageid SERIAL PRIMARY KEY,
  roomid VARCHAR REFERENCES room(roomid) NOT NULL,
  title VARCHAR NOT NULL,
  path VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  created TIMESTAMP NOT NULL,
  uploader VARCHAR REFERENCES account(id)
);
