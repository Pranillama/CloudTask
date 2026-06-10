// AWS Configuration
const AWS_CONFIG = {
    // Cognito Configuration
    region: 'us-east-2', // AWS region
    userPoolId: 'us-east-2_kXPdohPCD', //Cognito User Pool ID
    userPoolWebClientId: '7f67re6mdcm7g56p9jff7dspjl', // App Client ID
    
    // API Gateway Configuration
    apiEndpoint: 'https://ypzqe1ubbd.execute-api.us-east-2.amazonaws.com/prod', //API Gateway invoke URL 
};

window.AWS_CONFIG = AWS_CONFIG;
