import { UserModel } from '../../../generated/prisma/models/User';

export interface UserWhereUniqueInput {
  id?: number;
  email?: string;
  googleId?: string;
}

export interface UserCreateData {
  email: string;
  name?: string | null;
  avatar?: string | null;
  googleId?: string | null;
  hashedRefreshToken?: string | null;
}

export interface UserUpdateData {
  name?: string | null;
  avatar?: string | null;
  googleId?: string | null;
  hashedRefreshToken?: string | null;
}

export interface UserUpdateManyWhereInput {
  id?: number;
  hashedRefreshToken?: { not: null } | null | string;
}

export const USER_STORE = Symbol('USER_STORE');

export interface UserStore {
  findUnique(args: { where: UserWhereUniqueInput }): Promise<UserModel | null>;
  create(args: { data: UserCreateData }): Promise<UserModel>;
  update(args: { where: { id: number }; data: UserUpdateData }): Promise<UserModel>;
  updateMany(args: {
    where: UserUpdateManyWhereInput;
    data: UserUpdateData;
  }): Promise<{ count: number }>;
}
