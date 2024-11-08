export default {
  base: "./",
  build: {
    lib: {
      entry: "./src/main.js",
      name: "surf_seg",
      formats: ["umd"],
      fileName: "surf_seg",
    },
    rollupOptions: {
      external: ["vue"],
      output: {
        globals: {
          vue: "Vue",
        },
      },
    },
    outDir: "../surf_seg/module/serve",
    assetsDir: ".",
  },
};
