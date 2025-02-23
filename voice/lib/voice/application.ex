defmodule Voice.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    children = [
      VoiceWeb.Telemetry,
      Voice.Repo,
      {DNSCluster, query: Application.get_env(:voice, :dns_cluster_query) || :ignore},
      {Phoenix.PubSub, name: Voice.PubSub},
      # Start the Finch HTTP client for sending emails
      {Finch, name: Voice.Finch},
      # Start a worker by calling: Voice.Worker.start_link(arg)
      # {Voice.Worker, arg},
      # Start to serve requests, typically the last entry
      VoiceWeb.Endpoint
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: Voice.Supervisor]
    Supervisor.start_link(children, opts)
  end

  # Tell Phoenix to update the endpoint configuration
  # whenever the application is updated.
  @impl true
  def config_change(changed, _new, removed) do
    VoiceWeb.Endpoint.config_change(changed, removed)
    :ok
  end
end
