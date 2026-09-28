return {
  -- GitLens-style inline blame + gutter signs
  {
    "lewis6991/gitsigns.nvim",
    event = { "BufReadPre", "BufNewFile" },
    opts = {
      current_line_blame = true, -- inline blame, like GitLens
      current_line_blame_opts = {
        virt_text = true,
        virt_text_pos = "eol", -- show blame at end of line
        delay = 300,
      },
      current_line_blame_formatter = "<author>, <author_time:%Y-%m-%d> - <summary>",
      signs = {
        add = { text = "│" },
        change = { text = "│" },
        delete = { text = "_" },
        topdelete = { text = "‾" },
        changedelete = { text = "~" },
      },
    },
    keys = {
      {
        "<leader>gb",
        function()
          require("gitsigns").blame_line({ full = true })
        end,
        desc = "Git blame line",
      },
      {
        "<leader>gp",
        function()
          require("gitsigns").preview_hunk()
        end,
        desc = "Preview hunk",
      },
      {
        "<leader>gt",
        function()
          require("gitsigns").toggle_current_line_blame()
        end,
        desc = "Toggle inline blame",
      },
      {
        "]c",
        function()
          require("gitsigns").nav_hunk("next")
        end,
        desc = "Next hunk",
      },
      {
        "[c",
        function()
          require("gitsigns").nav_hunk("prev")
        end,
        desc = "Prev hunk",
      },
    },
  },

  -- Full git porcelain: blame column, log, diffs, staging
  {
    "tpope/vim-fugitive",
    cmd = { "Git", "Gclog", "Gdiffsplit", "Gvdiffsplit" },
    keys = {
      { "<leader>gs", ":Git<CR>", desc = "Git status" },
      { "<leader>gB", ":Git blame<CR>", desc = "Git blame (full column)" },
      { "<leader>gl", ":Gclog<CR>", desc = "Git log" },
    },
  },
}
