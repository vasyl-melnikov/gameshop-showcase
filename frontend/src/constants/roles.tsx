
export enum Roles {
    PARTIALLY_LOGGED_IN = 'partially_logged_in',
    USER = 'user',
    SUPPORT_MODERATOR = 'support_moderator',
    ADMIN = 'admin',
    ROOT_ADMIN = 'root_admin'

}

export const roleWeightMapping = {
  [Roles.PARTIALLY_LOGGED_IN]: 1,
  [Roles.USER]: 2,
  [Roles.SUPPORT_MODERATOR]: 3,
  [Roles.ADMIN]: 4,
  [Roles.ROOT_ADMIN]: 5,
};
