defmodule Voice.Repo do
  use Ecto.Repo,
    otp_app: :voice,
    adapter: Ecto.Adapters.Postgres
end
