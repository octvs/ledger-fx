{
  description = "Python application flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      runtimeDeps = with pkgs.python3Packages; [selectolax pandas httpx];
      buildDeps = with pkgs.python3Packages; [setuptools];
      selectolax = pkgs.python3Packages.buildPythonPackage rec {
        # TODO: Upstream
        pname = "selectolax";
        version = "0.3.28";
        src = pkgs.python3Packages.fetchPypi {
          inherit pname version;
          sha256 = "iuPalyYbV77VH6mwPEiJhfbc/y4uREcaqfXiwXzBxFo=";
        };
        doCheck = false;
      };
    in {
      packages = rec {
        ledger-fx = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-fx";
          version = "0.1";
          pyproject = true;
          propagatedBuildInputs = runtimeDeps ++ buildDeps;
          src = ./.;
        };
        default = ledger-fx;
      };

      devShells.default = pkgs.mkShell {buildInputs = runtimeDeps;};
    })
    // {
      overlays.default = final: prev: {ledger-fx = self.packages.${prev.system}.default;};
    };
}
