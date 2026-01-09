module.exports = {
    apps: [{
        name: 'n8n',
        script: './packages/cli/bin/n8n',
        cwd: '/Users/yoogeon/n8n',
        interpreter: '/Users/yoogeon/.nvm/versions/node/v22.21.1/bin/node',
        env: {
            N8N_COMMUNITY_PACKAGES_ENABLED: 'false',
            N8N_DEFAULT_LOCALE: 'ko',
            NODE_ENV: 'production'
        },
        autorestart: true,
        watch: false,
        max_memory_restart: '1G',
        log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
        error_file: '/Users/yoogeon/.n8n/logs/error.log',
        out_file: '/Users/yoogeon/.n8n/logs/out.log',
        merge_logs: true
    }]
};
