User service implemented in ModuleFolders/Service/User/:
- UserManager: profile management, CRUD operations, role/status updates, login history, preferences
- UserRepository: data access layer with find/create/update/delete methods
- Email templates added: email change, password change, account deletion, role change, account suspended/reacted
- Validators: username (3-20 chars), full_name, bio (500 chars), avatar_url
- Depends on: Auth models, PasswordManager, EmailService
