-- Test OK on grafana 9.2.4
-- Test OK on grafana 9.5.2

update user set password='93407fc3645ef57d602458b95b2e73f56ba03598e1f6090949ecaddff9bcbe108d089f47ed8002c7de046483622445bca18e', salt='fk1dssmCl3', rands='6AHy02LoVO', updated=datetime() where login='admin';
