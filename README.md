# Time Tracker

## Installation and run
```
git clone https://github.com/mohsen-hassani/tracker
cd tracker
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Authentication System
  - Authenticaiton class = Token Authentication



## Endpoints

| endpont                                     | methods          | description                                                                                                                                                                             |
|---------------------------------------------|------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| /api/v1/accounts/register/                  | POST             | Get email, password, first_name and last_name and register a user as inactive. An Email will send to user to activate her/his account                                                   |
| /api/v1/accounts/activate/<key>             | GET              | Find user by the activation_key and activate user if the activation is not expired                                                                                                      |
| /api/v1/accounts/login/                     | POST             | Get username and password and return Token if the credentials is true and user is active                                                                                                |
| /api/v1/accounts/profile/                   | GET, PUT         | Retrieve email, first_name and last_name or Update first_name and last_name                                                                                                             |
| /api/v1/projects/                           | GET, POST        | Get all projects belong to user or Create a new project by passing title as post parameter. You can pass deleted=true as a query parameter to include deleted projects as well          |
| /api/v1/projects/<uuid>/                    | GET, PUT, DELETE | Get, Update or Delete a project by UUID. Delete process is just logical and data will not delete from database                                                                          |
| /api/v1/projects/<uuid>/restore/            | PATCH            | Restore a deleted project                                                                                                                                                               |
| /api/v1/projects/<uuid>/tasks/              | GET, POST        | Get all tasks of a project or create a new one using this field: title                                                                                                                  |
| /api/v1/projects/<uuid>/tasks/<uuid>/       | GET, PUT, DELETE | Get a task, update it or delete it from database.                                                                                                                                       |
| /api/v1/projects/<uuid>/tasks/<uuid>/start/ | PATCH            | Start tracking time for a task by creating a new time entry without an end time. Note that, to start multiple tasks at the same time, you should enable ProjectSetting.concurrent_tasks |
| /api/v1/projects/<uuid>/tasks/<uuid>/stop/  | PATCH            | Find all started time entries for that task and change their end time to now                                                                                                            |
| /api/v1/projects/<uuid>/stop-all-tasks/     | PUT              | Stop all running tasks related to given project                                                                                                                                         |