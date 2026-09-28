return {
  -- catppuccin
  {
    "catppuccin/nvim",
    name = "catppuccin",
    lazy = true,
    opts = {
      flavour = "mocha",
    },
  },

  -- tokyonight
  {
    "folke/tokyonight.nvim",
    lazy = true,
    opts = {
      style = "moon",
    },
  },

  -- kanagawa
  { "rebelot/kanagawa.nvim" },

  -- monokai-pro
  { "loctvl842/monokai-pro.nvim", lazy = false, priority = 1000 },

  -- configure LazyVim to load kanagawa
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "monokai-pro",
    },
  },
}
