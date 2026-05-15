2026-05-15 21:44:57.632 CEST
Starting new instance. Reason: DEPLOYMENT_ROLLOUT - Instance started due to traffic shifting between revisions due to deployment, traffic split adjustment, or deployment health check.
2026-05-15 21:45:01.736 CEST
Container called exit(0).
2026-05-15 21:45:01.813 CEST
Default STARTUP TCP probe failed 1 time consecutively for container "placeholder-1" on port 8080. The instance was not started. Connection failed with status CANCELLED.
2026-05-15 21:45:01.826 CEST

Cloud Run

ReplaceService

aichatbox-00035-kjq
Ready condition status changed to False for Revision aichatbox-00035-kjq with message: The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout. This can happen when the container port is misconfigured or if the timeout is too short. The health check timeout can be extended. Logs for this revision might contain more information.  Logs URL: https://console.cloud.google.com/logs/viewer?project=my-project-claude-496115&resource=cloud_run_revision/service_name/aichatbox/revision_name/aichatbox-00035-kjq&advancedFilter=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22aichatbox%22%0Aresource.labels.revision_name%3D%22aichatbox-00035-kjq%22  For more troubleshooting guidance, see https://cloud.google.com/run/docs/troubleshooting#container-failed-to-start
2026-05-15 21:45:01.902 CEST

Cloud Run

ReplaceService

aichatbox
Ready condition status changed to False for Service aichatbox with message: The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout. This can happen when the container port is misconfigured or if the timeout is too short. The health check timeout can be extended. Logs for this revision might contain more information.  Logs URL: https://console.cloud.google.com/logs/viewer?project=my-project-claude-496115&resource=cloud_run_revision/service_name/aichatbox/revision_name/aichatbox-00035-kjq&advancedFilter=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22aichatbox%22%0Aresource.labels.revision_name%3D%22aichatbox-00035-kjq%22  For more troubleshooting guidance, see https://cloud.google.com/run/docs/troubleshooting#container-failed-to-start
