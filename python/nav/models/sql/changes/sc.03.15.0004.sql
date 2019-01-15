-- Do the needed changes to migrate subcat to netboxgroup and remove
-- category limitation.

ALTER TABLE subcat DROP catid;
ALTER TABLE subcat RENAME TO netboxgroup;
ALTER TABLE netboxgroup RENAME subcatid TO netboxgroupid;

UPDATE matchfield SET
  name='Group',
  value_id='netboxgroup.netboxgroupid',
  value_name='netboxgroup.descr',
  value_sort='netboxgroup.descr',
  description='Group: netboxes may belong to a group that is independent of type and category'
  WHERE id=14;

