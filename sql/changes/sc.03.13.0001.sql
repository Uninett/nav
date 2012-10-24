alter table origin drop constraint origin_category_fkey;
alter table origin drop column category cascade;
alter table category drop constraint category_pkey;
alter table category add category_id SERIAL PRIMARY KEY NOT NULL;
alter table origin add column category integer REFERENCES category(category_id) ON DELETE SET NULL ON UPDATE CASCADE;
alter table category alter column category set not null;
alter table category add constraint category_uniq UNIQUE(category);
-- Need to rename columns to avoid name-crash in djnago with
-- netbox-catehory
alter table category rename column category to cat_name;
alter table origin rename column category to log_category;
