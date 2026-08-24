import { UserModel } from '../../../generated/prisma/models/User';
import {
  UserCreateData,
  UserStore,
  UserUpdateData,
  UserUpdateManyWhereInput,
  UserWhereUniqueInput,
} from './user.store.interface';

export class MemoryUserStore implements UserStore {
  private users: UserModel[] = [];
  private nextId = 1;

  async findUnique(args: {
    where: UserWhereUniqueInput;
  }): Promise<UserModel | null> {
    const user = this.users.find((u) => {
      if (args.where.id !== undefined && u.id === args.where.id) return true;
      if (args.where.email !== undefined && u.email === args.where.email)
        return true;
      if (
        args.where.googleId !== undefined &&
        u.googleId === args.where.googleId
      )
        return true;
      return false;
    });

    return user ? { ...user } : null;
  }

  async create(args: { data: UserCreateData }): Promise<UserModel> {
    const now = new Date();
    const user: UserModel = {
      id: this.nextId++,
      email: args.data.email,
      name: args.data.name ?? null,
      avatar: args.data.avatar ?? null,
      googleId: args.data.googleId ?? null,
      hashedRefreshToken: args.data.hashedRefreshToken ?? null,
      createdAt: now,
      updatedAt: now,
    };
    this.users.push(user);
    return { ...user };
  }

  async update(args: {
    where: { id: number };
    data: UserUpdateData;
  }): Promise<UserModel> {
    const index = this.users.findIndex((u) => u.id === args.where.id);
    if (index === -1) {
      throw new Error(
        `User with ID #${args.where.id} not found in memory store`,
      );
    }

    const current = this.users[index];
    const updated: UserModel = {
      ...current,
      name: args.data.name !== undefined ? args.data.name : current.name,
      avatar:
        args.data.avatar !== undefined ? args.data.avatar : current.avatar,
      googleId:
        args.data.googleId !== undefined
          ? args.data.googleId
          : current.googleId,
      hashedRefreshToken:
        args.data.hashedRefreshToken !== undefined
          ? args.data.hashedRefreshToken
          : current.hashedRefreshToken,
      updatedAt: new Date(),
    };

    this.users[index] = updated;
    return { ...updated };
  }

  async updateMany(args: {
    where: UserUpdateManyWhereInput;
    data: UserUpdateData;
  }): Promise<{ count: number }> {
    let count = 0;

    this.users = this.users.map((u) => {
      let matches = true;
      if (args.where.id !== undefined && u.id !== args.where.id) {
        matches = false;
      }
      if (
        args.where.hashedRefreshToken &&
        typeof args.where.hashedRefreshToken === 'object'
      ) {
        if (
          'not' in args.where.hashedRefreshToken &&
          args.where.hashedRefreshToken.not === null
        ) {
          if (u.hashedRefreshToken === null) {
            matches = false;
          }
        }
      }

      if (matches) {
        count++;
        return {
          ...u,
          hashedRefreshToken:
            args.data.hashedRefreshToken !== undefined
              ? args.data.hashedRefreshToken
              : u.hashedRefreshToken,
          updatedAt: new Date(),
        };
      }
      return u;
    });

    return { count };
  }

  reset() {
    this.users = [];
    this.nextId = 1;
  }
}
