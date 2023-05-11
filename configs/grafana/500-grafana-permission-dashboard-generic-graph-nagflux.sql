-- Test OK on grafana 9.2.4
-- Test OK on grafana 9.5.2

insert into permission (
    id, role_id, action, scope, created, updated
) values (
    1, 1, 'dashboards:read', 'dashboards:uid:_hdUoYR4k', datetime(), datetime()
);
