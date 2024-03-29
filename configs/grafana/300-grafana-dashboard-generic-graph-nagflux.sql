-- Test OK on grafana 9.2.4
-- Test OK on grafana 9.5.2

insert into dashboard (
    id, version, slug, title,
    org_id, created, updated, updated_by, created_by, gnet_id, plugin_id, folder_id,
    is_folder, has_acl, uid, is_public,
    data
) values (
    1, 0, 'generic-graph-nagflux', 'generic-graph-nagflux',
    1, datetime(), datetime(), 1, 1, 0, '', 0, 0, 0, '_hdUoYR4k', 1,
    '{"annotations":{"list":[{"builtIn":1,"datasource":{"type":"datasource","uid":"grafana"},"enable":true,"hide":true,"iconColor":"rgba(0, 211, 255, 1)","name":"Annotations \u0026 Alerts","target":{"limit":100,"matchAny":false,"tags":[],"type":"dashboard"},"type":"dashboard"}]},"editable":true,"fiscalYearStartMonth":0,"graphTooltip":0,"id":1,"links":[],"liveNow":false,"panels":[{"datasource":{"type":"influxdb","uid":"IHQqRqynk"},"description":"","fieldConfig":{"defaults":{"color":{"mode":"palette-classic"},"custom":{"axisCenteredZero":false,"axisColorMode":"text","axisLabel":"","axisPlacement":"auto","barAlignment":0,"drawStyle":"line","fillOpacity":10,"gradientMode":"none","hideFrom":{"legend":false,"tooltip":false,"viz":false},"lineInterpolation":"linear","lineWidth":1,"pointSize":5,"scaleDistribution":{"type":"linear"},"showPoints":"never","spanNulls":false,"stacking":{"group":"A","mode":"none"},"thresholdsStyle":{"mode":"off"}},"links":[],"mappings":[],"thresholds":{"mode":"absolute","steps":[{"color":"green","value":null},{"color":"red","value":80}]},"unit":"short"},"overrides":[{"matcher":{"id":"byName","options":"load1 "},"properties":[{"id":"color","value":{"fixedColor":"#edc240","mode":"fixed"}}]},{"matcher":{"id":"byName","options":"load5 "},"properties":[{"id":"color","value":{"fixedColor":"#afd8f8","mode":"fixed"}}]},{"matcher":{"id":"byName","options":"load15 "},"properties":[{"id":"color","value":{"fixedColor":"#cb4b4b","mode":"fixed"}}]},{"matcher":{"id":"byRegexp","options":"/ B$/"},"properties":[{"id":"unit","value":"bytes"}]}]},"gridPos":{"h":11,"w":24,"x":0,"y":0},"id":2,"interval":"5m","options":{"legend":{"calcs":["mean","lastNotNull","max","min"],"displayMode":"table","placement":"bottom","showLegend":true},"tooltip":{"mode":"multi","sort":"none"}},"pluginVersion":"9.2.1","targets":[{"alias":"$tag_performanceLabel $tag_unit","datasource":{"type":"influxdb","uid":"IHQqRqynk"},"groupBy":[{"params":["$__interval"],"type":"time"},{"params":["performanceLabel"],"type":"tag"},{"params":["unit"],"type":"tag"},{"params":["null"],"type":"fill"}],"measurement":"metrics","orderByTime":"ASC","policy":"default","refId":"A","resultFormat":"time_series","select":[[{"params":["value"],"type":"field"},{"params":[],"type":"mean"}]],"tags":[{"key":"host","operator":"=~","value":"/^$device$/"},{"condition":"AND","key":"service","operator":"=~","value":"/^$indicator$/"}]}],"title":"$device/$indicator","type":"timeseries"}],"refresh":"","schemaVersion":38,"style":"dark","tags":[],"templating":{"list":[{"datasource":{"type":"influxdb","uid":"IHQqRqynk"},"definition":"show tag values with key = \"host\";","hide":0,"includeAll":false,"multi":false,"name":"device","options":[],"query":"show tag values with key = \"host\";","refresh":1,"regex":"","skipUrlSync":false,"sort":1,"tagValuesQuery":"","tagsQuery":"","type":"query","useTags":false},{"datasource":{"type":"influxdb","uid":"IHQqRqynk"},"definition":"show tag values on nagflux with key = \"service\" where host =~ /^$device$/;","hide":0,"includeAll":false,"multi":false,"name":"indicator","options":[],"query":"show tag values on nagflux with key = \"service\" where host =~ /^$device$/;","refresh":1,"regex":"","skipUrlSync":false,"sort":1,"tagValuesQuery":"","tagsQuery":"","type":"query","useTags":false}]},"time":{"from":"now-24h","to":"now"},"timepicker":{"refresh_intervals":["10s","30s","1m","5m","15m","30m","1h","2h","1d"]},"timezone":"","title":"generic-graph-nagflux","uid":"_hdUoYR4k","version":5,"weekStart":""}'
);

insert into dashboard_version (
    dashboard_id, parent_version, restored_from, version, created, created_by,
    message, data
) values (
    1, 0, 0, 1, (select created from dashboard where id=1), 1,
    'initial version',
    (select data from dashboard where id=1)
);
