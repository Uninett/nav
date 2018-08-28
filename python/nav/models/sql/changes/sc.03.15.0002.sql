-- Create table for images

CREATE TABLE manage.image (
  imageid SERIAL PRIMARY KEY,
  roomid VARCHAR REFERENCES room(roomid) NOT NULL,
  title VARCHAR NOT NULL,
  path VARCHAR NOT NULL,
  name VARCHAR NOT NULL,
  created TIMESTAMP NOT NULL,
  uploader INT REFERENCES account(id),
  priority INT
);
