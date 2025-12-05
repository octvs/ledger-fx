{
  description = "Python application flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} ({...}: {
      systems = import inputs.systems;
      perSystem = {pkgs, ...}: let
        dependencies = with pkgs.python3.pkgs; [selectolax pandas httpx];
        selectolax = pkgs.python3Packages.buildPythonPackage rec {
          # TODO: Upstream
          pname = "selectolax";
          version = "0.3.28";
          pyproject = true;
          src = pkgs.python3Packages.fetchPypi {
            inherit pname version;
            sha256 = "iuPalyYbV77VH6mwPEiJhfbc/y4uREcaqfXiwXzBxFo=";
          };
          build-system = with pkgs.python3.pkgs; [setuptools];
          doCheck = false;
        };
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-fx";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pkgs.python3.pkgs; [setuptools];
          inherit dependencies;
        };
      };
    });
}
