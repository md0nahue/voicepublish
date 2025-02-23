require 'sinatra'
require 'aws-sdk-s3'
require 'securerandom'
require 'json'

# Configure AWS S3 client
# It's recommended to use environment variables or AWS IAM roles for credentials
s3 = Aws::S3::Client.new(
  region: 'us-east-1',
  access_key_id: ENV.fetch('VOICE_PUBLISH_KEY_ID'),       # Ensure this is set in your environment
  secret_access_key:  ENV.fetch('VOICE_PUBLISH_KEY_SECRET') # Ensure this is set in your environment
)

BUCKET_NAME = 'voicepublish'

# Enable CORS (if necessary)
before do
  headers 'Access-Control-Allow-Origin' => '*',
          'Access-Control-Allow-Methods' => 'PUT, GET, OPTIONS',
          'Access-Control-Allow-Headers' => 'Content-Type'
end

# Handle OPTIONS requests for CORS preflight checks
options '*' do
  200
end

# Endpoint to generate a presigned URL for audio uploads
get '/get_presigned_url' do
  content_type :json

  begin
    # Generate a unique object key using a random UUID and the current timestamp
    object_key = "audio/#{SecureRandom.uuid}-#{Time.now.to_i}.ogg"

      mime_type = params['mime_type']
        mime_type ||= 'application/octet-stream'
    # Generate the presigned URL
    # The URL will be valid for PUT requests (uploads) for 60 seconds
    presigner = Aws::S3::Presigner.new(client: s3)
    url = presigner.presigned_url(
      :put_object,
      bucket: BUCKET_NAME,
      key: object_key,
      expires_in: 60,                 # URL expiration time in seconds
      content_type: mime_type       # Ensure the correct content type
    )

    # Respond with the presigned URL and the object key
    {
      url: url,
      key: object_key
    }.to_json

  rescue Aws::S3::Errors::ServiceError => e
    status 500
    { error: "Failed to generate presigned URL: #{e.message}" }.to_json
  end
end

# (Optional) Endpoint to verify uploaded file or perform additional actions
# get '/verify-upload/:key' do
#   # Implement verification logic if needed
# end