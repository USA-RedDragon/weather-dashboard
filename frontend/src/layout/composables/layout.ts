import { toRefs, reactive } from 'vue';

const layoutConfig = reactive({
  theme: 'mdc-dark-indigo',
  scale: 16,
});

export function useLayout() {
  const changeThemeSettings = (theme: string) => {
    layoutConfig.theme = theme;
  };

  const setScale = (scale: number) => {
    layoutConfig.scale = scale;
    window.localStorage.setItem('scale', scale.toString());
  };

  return {
    layoutConfig: toRefs(layoutConfig),
    changeThemeSettings,
    setScale,
  };
}
