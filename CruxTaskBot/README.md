# CruxTaskBot

CruxTaskBot is a powerful Discord bot designed for the CRUx server, providing a wide range of task management and automation features to streamline the club's workflow. It also comes with a vscode extension that can be used alongside the bot.

## Features

### Task Management
- **Create To-Do Checklists:** Members can create weekly to-do checklists divided by projects. Each task includes a title, short one-line description, estimated time of completion (deadline), and is tagged under domain and project.
- **Database Integration:** All the data is stored within an SQLite database.
- **Project Task Sheets:** Members can view project-specific task sheets to see the progress of tasks under that project.
- **Organized Display:** Tasks are displayed in a structured format, showcasing project names, domains, assigned members, and their respective tasks.

### Daily Reminders
- **Automated Daily Updates:** Every day at 00:00, the bot automatically displays every project's weekly task sheet in its respective channel.
- **Task Reminders:** The Bot sends email reminders to individuals two days before their task deadlines to help them stay on track.

### Monthly Review Meetings
- **Monthly Meeting Automation:** Host monthly review meetings by displaying a list of dates and timings provided by the senate in the #announcements channel.
- **Voting Mechanism:** Allow users to vote on meeting timings, ensuring convenient scheduling for all participants.

### Extension Integration
- **Visual Studio Code Extension:** A VS Code extension is available for crux members to seamlessly mark tasks as complete, or in progress, directly within their code editor.
- **Real-time Updates:** The bot reflects these changes in the Discord server, keeping everyone informed of task progress.

### GitHub Integration
- **Track Pull Requests and Issues:** CruxTaskBot monitors user-generated pull requests and issues. When commits are pushed, the bot displays the relevant PR or issue in the Discord server.
- **User Activity:** Allow users to view the activity, including authored pull requests and issues, of a specific user when prompted.

### Documentation Generation
- **Generate Documentation:** Create documentation files in Markdown format (.md) for source code files. The bot & extension can automatically generate documentation upon request.
- **Automatic push to github:** The bot adds the generated documentation to a the bot_docs branch in the repository.

### Google Calendar Integration
- **Google Calendar Tasks:** Users can add tasks to their weekly Google Calendar using the bot. For testing purposes, the bot uses a pre-configured GCal token, eliminating the need to prompt users.
