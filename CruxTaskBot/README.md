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

## Installation and Hosting Guide

**Follow these steps to install and host CruxTaskBot:**

1. **Clone the Repository**
   - Begin by cloning the CruxTaskBot repository to your local machine using the following command:
     ```
     git clone https://github.com/CWSwastik/CRUx-Round-3-Submission
     ```

2. **Navigate to the Bot Directory**
   - Change your working directory to the CruxTaskBot folder:
     ```
     cd CruxTaskBot
     ```

3. **Configure Environment Variables**

   - Create a `.env` file based on the provided `.env.example` file.
   
   - For each parameter in the `.env` file, follow these instructions:
   
     1. **Discord Token**:
        - Obtain a Discord bot token by creating a new bot application on the [Discord Developer Portal](https://discord.com/developers/applications).
        - Refer to https://discordpy.readthedocs.io/en/stable/discord.html for detailed instructions.
        - **IMPORTANT**: When inviting the bot to your server make sure the `bot` and `applications.commands` scope are turned on and the bot is invited with `Administrator` permisions.
        - Set the Discord token as the value for `DISCORD_TOKEN` in the `.env` file.

     2. **Email Setup**:
        - If you are using Gmail and have two-factor authentication (2FA) enabled, your email password must be replaced with a 16-digit App Password. Learn how to generate an App Password for SMTP [here](https://support.google.com/accounts/answer/185833?hl=en).
        - Set your email address as the value for `EMAIL_ID` and your generated email App Password as the value for `EMAIL_PASSWORD` in the `.env` file.
        
     3. **OpenAI API Key**:
        - Obtain an API key from OpenAI and set it as the value for `OPENAI_API_KEY` in the `.env` file.

     4. **GitHub Integration**:
        - Create a GitHub App with the required permissions:
           - Webhooks: read & write
           - Workflows: read & write
           - Contents: read & write
        - Save the app's private key as `github_private_key.pem` in the `CruxTaskBot` directory.
        - Install the GitHub App on your organization.
        - Set the GitHub App ID as the value for `GITHUB_APP_ID` and the Installation ID as the value for `GITHUB_INSTALLATION_ID` in the `.env` file.
        - The Installation ID can be found from the url `https://github.com/organizations/[ORG]/settings/installations/[INSTALATION ID]`
          
     5. **Local Testing with Ngrok (Optional)**:
        - If you are running the bot locally for testing, you will need to use Ngrok to expose the webserver publically.
          ```bash
              ngrok http 8080
          ```
        - After obtaining the Ngrok URL, set it as the value for `WEBSERVER_URL` in the `.env` file.

     6. **Google Calendar Setup**:
        - Obtain the `credentials.json` file (for detailed instructions [click here](https://developers.google.com/calendar/api/quickstart/python)) and save it in the `CruxTaskBot` directory.  

4. **Run the Bot**
   - You are now ready to run CruxTaskBot. You can run it using the following command
   ```bash
   python main.py
   ```

**Follow these steps to install and run the CruxTaskExtension (the vscode extension):**
1. Download the `crux-task-extension-1.0.0.vsix` from [this](https://https://drive.google.com/file/d/1N4EXxkDnNYlVq7G7mK_QVXQfhQLA08l5/view?usp=sharing) google drive link.
2. Install the Extension from the vsix file. For reference, https://code.visualstudio.com/docs/editor/extension-marketplace#_install-from-a-vsix

*For detailed guidance on each step, please refer to the relevant documentation and references provided above.*

## Usage

### Bot
You can view the bot's commands by typing a / and selecting the Bot. Run the command by clicking on it and providing the required parameters.

### Extension
Open the command palette with `Ctrl+P` and run either `> Show Crux Task Window` or `> Generate Document`
   - You may need to wait a while for the extension to startup for the first time (it takes time to install the dependencies)
Next, follow the steps as prompted by the extension.
